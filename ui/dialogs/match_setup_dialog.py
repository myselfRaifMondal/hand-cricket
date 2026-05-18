"""Pre-match setup dialog for team, toss, lineup, and opening players."""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from controllers.match_controller import MatchController


class MatchSetupDialog(QDialog):
    """Collect mandatory pre-match setup details before first ball."""

    def __init__(self, parent: Optional[QDialog] = None, presets: Optional[dict[str, Any]] = None) -> None:
        super().__init__(parent)
        self._presets = presets or {}
        self.setWindowTitle("Match Setup")
        self.setMinimumWidth(760)
        self._build_ui()
        if self._presets:
            self._apply_presets(self._presets)
        else:
            self._refresh_team_dependent_inputs()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(14)

        heading = QLabel("Complete setup before starting the match")
        heading.setObjectName("screenTitle")
        root.addWidget(heading)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        basics = QFormLayout()
        self.home_team_edit = QLineEdit("Falcons")
        self.away_team_edit = QLineEdit("Titans")
        self.overs_spin = QSpinBox()
        self.overs_spin.setRange(1, 50)
        self.overs_spin.setValue(5)
        self.wickets_spin = QSpinBox()
        self.wickets_spin.setRange(1, 10)
        self.wickets_spin.setValue(4)
        basics.addRow("Home team", self.home_team_edit)
        basics.addRow("Away team", self.away_team_edit)
        basics.addRow("Overs", self.overs_spin)
        basics.addRow("Wickets", self.wickets_spin)

        toss = QFormLayout()
        self.toss_winner_combo = QComboBox()
        self.toss_decision_combo = QComboBox()
        self.toss_decision_combo.addItems(["bat", "bowl"])
        toss.addRow("Toss winner", self.toss_winner_combo)
        toss.addRow("Toss decision", self.toss_decision_combo)

        lineup = QFormLayout()
        self.home_order_edit = QTextEdit("A. Ray, K. Sen, M. Roy, P. Das, T. Khan, L. Bose")
        self.away_order_edit = QTextEdit("R. Das, J. Ali, N. Paul, S. Roy, B. Khan, Z. Noor")
        self.home_order_edit.setPlaceholderText("Comma-separated batting order")
        self.away_order_edit.setPlaceholderText("Comma-separated batting order")
        self.home_order_edit.setFixedHeight(120)
        self.away_order_edit.setFixedHeight(120)
        lineup.addRow("Home batting order", self.home_order_edit)
        lineup.addRow("Away batting order", self.away_order_edit)

        opening = QFormLayout()
        self.striker_combo = QComboBox()
        self.opening_bowler_combo = QComboBox()
        opening.addRow("Opening striker", self.striker_combo)
        opening.addRow("Opening bowler", self.opening_bowler_combo)

        grid.addLayout(basics, 0, 0)
        grid.addLayout(toss, 0, 1)
        grid.addLayout(lineup, 1, 0)
        grid.addLayout(opening, 1, 1)
        root.addLayout(grid)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.home_team_edit.textChanged.connect(self._refresh_team_dependent_inputs)
        self.away_team_edit.textChanged.connect(self._refresh_team_dependent_inputs)
        self.toss_winner_combo.currentTextChanged.connect(self._refresh_opening_player_inputs)
        self.toss_decision_combo.currentTextChanged.connect(self._refresh_opening_player_inputs)
        self.home_order_edit.textChanged.connect(self._refresh_opening_player_inputs)
        self.away_order_edit.textChanged.connect(self._refresh_opening_player_inputs)

    def _parse_order(self, text: str) -> list[str]:
        return [name.strip() for name in text.replace("\n", ",").split(",") if name.strip()]

    def _apply_presets(self, presets: dict[str, Any]) -> None:
        home_team = str(presets.get("home_team_name", "")).strip()
        away_team = str(presets.get("away_team_name", "")).strip()
        if home_team:
            self.home_team_edit.setText(home_team)
        if away_team:
            self.away_team_edit.setText(away_team)

        overs = presets.get("overs")
        if isinstance(overs, int):
            self.overs_spin.setValue(max(self.overs_spin.minimum(), min(self.overs_spin.maximum(), overs)))

        wickets = presets.get("max_wickets")
        if isinstance(wickets, int):
            self.wickets_spin.setValue(max(self.wickets_spin.minimum(), min(self.wickets_spin.maximum(), wickets)))

        home_order = presets.get("home_batting_order")
        away_order = presets.get("away_batting_order")
        if isinstance(home_order, list):
            self.home_order_edit.setPlainText(", ".join(str(name).strip() for name in home_order if str(name).strip()))
        if isinstance(away_order, list):
            self.away_order_edit.setPlainText(", ".join(str(name).strip() for name in away_order if str(name).strip()))

        self._refresh_team_dependent_inputs()

        toss_winner_name = str(presets.get("toss_winner_name", "")).strip()
        if toss_winner_name:
            index = self.toss_winner_combo.findText(toss_winner_name)
            if index >= 0:
                self.toss_winner_combo.setCurrentIndex(index)

        toss_decision = str(presets.get("toss_decision", "")).strip()
        if toss_decision:
            index = self.toss_decision_combo.findText(toss_decision)
            if index >= 0:
                self.toss_decision_combo.setCurrentIndex(index)

        self._refresh_opening_player_inputs()

        opening_striker = str(presets.get("opening_striker", "")).strip()
        opening_bowler = str(presets.get("opening_bowler", "")).strip()
        if opening_striker:
            index = self.striker_combo.findText(opening_striker)
            if index >= 0:
                self.striker_combo.setCurrentIndex(index)
        if opening_bowler:
            index = self.opening_bowler_combo.findText(opening_bowler)
            if index >= 0:
                self.opening_bowler_combo.setCurrentIndex(index)

    def _refresh_team_dependent_inputs(self) -> None:
        home = self.home_team_edit.text().strip() or "Home"
        away = self.away_team_edit.text().strip() or "Away"
        self.toss_winner_combo.blockSignals(True)
        self.toss_winner_combo.clear()
        self.toss_winner_combo.addItems([home, away])
        self.toss_winner_combo.blockSignals(False)
        self._refresh_opening_player_inputs()

    def _batting_and_bowling_team_names(self) -> tuple[str, str]:
        home = self.home_team_edit.text().strip() or "Home"
        away = self.away_team_edit.text().strip() or "Away"
        toss_winner = self.toss_winner_combo.currentText() or home
        decision = self.toss_decision_combo.currentText() or "bat"
        if (toss_winner == home and decision == "bat") or (toss_winner == away and decision == "bowl"):
            return home, away
        return away, home

    def _refresh_opening_player_inputs(self) -> None:
        home = self.home_team_edit.text().strip() or "Home"
        away = self.away_team_edit.text().strip() or "Away"
        home_order = self._parse_order(self.home_order_edit.toPlainText())
        away_order = self._parse_order(self.away_order_edit.toPlainText())
        batting_team, bowling_team = self._batting_and_bowling_team_names()

        batting_order = home_order if batting_team == home else away_order
        bowling_order = away_order if bowling_team == away else home_order

        self.striker_combo.clear()
        self.opening_bowler_combo.clear()
        self.striker_combo.addItems(batting_order)
        self.opening_bowler_combo.addItems(bowling_order)

        if batting_order:
            self.striker_combo.setCurrentIndex(0)

    def _on_accept(self) -> None:
        home = self.home_team_edit.text().strip()
        away = self.away_team_edit.text().strip()
        home_order = self._parse_order(self.home_order_edit.toPlainText())
        away_order = self._parse_order(self.away_order_edit.toPlainText())
        striker = self.striker_combo.currentText().strip()
        opening_bowler = self.opening_bowler_combo.currentText().strip()

        if not home or not away:
            QMessageBox.warning(self, "Validation", "Both team names are required.")
            return
        if home == away:
            QMessageBox.warning(self, "Validation", "Team names must be different.")
            return
        required_players = self.wickets_spin.value() + 1
        if len(home_order) < required_players or len(away_order) < required_players:
            QMessageBox.warning(
                self,
                "Validation",
                f"Each team needs at least {required_players} players in batting order for {self.wickets_spin.value()} wickets.",
            )
            return
        if not striker:
            QMessageBox.warning(self, "Validation", "Choose an opening batter.")
            return
        if not opening_bowler:
            QMessageBox.warning(self, "Validation", "Choose an opening bowler.")
            return

        self.accept()

    def payload(self) -> MatchController.SetupPayload:
        return MatchController.SetupPayload(
            home_team_name=self.home_team_edit.text().strip(),
            away_team_name=self.away_team_edit.text().strip(),
            overs=self.overs_spin.value(),
            max_wickets=self.wickets_spin.value(),
            toss_winner_name=self.toss_winner_combo.currentText().strip(),
            toss_decision=self.toss_decision_combo.currentText().strip(),
            home_batting_order=self._parse_order(self.home_order_edit.toPlainText()),
            away_batting_order=self._parse_order(self.away_order_edit.toPlainText()),
            opening_striker=self.striker_combo.currentText().strip(),
            opening_bowler=self.opening_bowler_combo.currentText().strip(),
        )
