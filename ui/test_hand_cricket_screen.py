"""Test Hand Cricket preset screen."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TestHandCricketScreen(QWidget):
    """Collects a Test-mode profile and opens setup with prefilled values."""

    setup_preset_requested = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Test Hand Cricket")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Create a Test profile and open Match Setup with these defaults.")
        subtitle.setObjectName("screenSubtitle")

        form = QFormLayout()
        self.profile_name_edit = QLineEdit("Classic Test")
        self.home_team_edit = QLineEdit("Falcons")
        self.away_team_edit = QLineEdit("Titans")

        self.overs_spin = QSpinBox()
        self.overs_spin.setRange(1, 300)
        self.overs_spin.setValue(90)

        self.wickets_spin = QSpinBox()
        self.wickets_spin.setRange(1, 10)
        self.wickets_spin.setValue(10)

        self.home_order_edit = QTextEdit(
            "A. Ray, K. Sen, M. Roy, P. Das, T. Khan, L. Bose, S. Mitra, N. Iqbal, R. Jain, V. Paul, D. Karim"
        )
        self.away_order_edit = QTextEdit(
            "R. Das, J. Ali, N. Paul, S. Roy, B. Khan, Z. Noor, H. Sami, P. Nair, C. Dutt, E. Khan, U. Malik"
        )
        self.home_order_edit.setFixedHeight(110)
        self.away_order_edit.setFixedHeight(110)

        form.addRow("Profile", self.profile_name_edit)
        form.addRow("Home team", self.home_team_edit)
        form.addRow("Away team", self.away_team_edit)
        form.addRow("Overs", self.overs_spin)
        form.addRow("Wickets", self.wickets_spin)
        form.addRow("Home batting order", self.home_order_edit)
        form.addRow("Away batting order", self.away_order_edit)

        actions = QHBoxLayout()
        self.apply_button = QPushButton("Open Setup With Test Profile")
        self.apply_button.clicked.connect(self._emit_preset)
        actions.addWidget(self.apply_button)
        actions.addStretch()

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(form)
        root.addLayout(actions)
        root.addStretch(1)

    @staticmethod
    def _parse_order(text: str) -> list[str]:
        return [name.strip() for name in text.replace("\n", ",").split(",") if name.strip()]

    def _emit_preset(self) -> None:
        home_team = self.home_team_edit.text().strip() or "Home"
        away_team = self.away_team_edit.text().strip() or "Away"
        home_order = self._parse_order(self.home_order_edit.toPlainText())
        away_order = self._parse_order(self.away_order_edit.toPlainText())

        toss_winner = home_team
        toss_decision = "bat"
        batting_order = home_order
        bowling_order = away_order

        preset = {
            "profile_name": self.profile_name_edit.text().strip() or "Test Profile",
            "home_team_name": home_team,
            "away_team_name": away_team,
            "overs": self.overs_spin.value(),
            "max_wickets": self.wickets_spin.value(),
            "toss_winner_name": toss_winner,
            "toss_decision": toss_decision,
            "home_batting_order": home_order,
            "away_batting_order": away_order,
            "opening_striker": batting_order[0] if batting_order else "",
            "opening_bowler": bowling_order[0] if bowling_order else "",
        }
        self.setup_preset_requested.emit(preset)
