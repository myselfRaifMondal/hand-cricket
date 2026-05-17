"""Live match screen with real-time scoreboard and two input pads."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from controllers.match_controller import MatchController
from ui.widgets.number_pad import NumberPad
from ui.widgets.stat_card import StatCard


class MatchScreen(QWidget):
    """Live scoring surface for ball-by-ball administration."""

    def __init__(self, controller: MatchController) -> None:
        super().__init__()
        self.controller = controller
        self._pulse_color = QColor("#f59e0b")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(18)

        title = QLabel("Live Match Desk")
        title.setObjectName("screenTitle")
        self.summary_label = QLabel("Ready for kickoff")
        self.summary_label.setObjectName("screenSubtitle")

        scoreboard = QHBoxLayout()
        scoreboard.setSpacing(12)
        self.score_card = StatCard("Score", "0/0", "score")
        self.overs_card = StatCard("Overs", "0.0", "muted")
        self.target_card = StatCard("Target", "-", "accent")
        self.rr_card = StatCard("Required RR", "0.00", "accent")
        for card in [self.score_card, self.overs_card, self.target_card, self.rr_card]:
            scoreboard.addWidget(card)

        pads_layout = QHBoxLayout()
        pads_layout.setSpacing(16)

        batting_layout = QVBoxLayout()
        batting_label = QLabel("Batting Input")
        batting_label.setObjectName("sectionLabel")
        self.batting_pad = NumberPad("batting")
        batting_layout.addWidget(batting_label)
        batting_layout.addWidget(self.batting_pad)

        bowling_layout = QVBoxLayout()
        bowling_label = QLabel("Bowling Input")
        bowling_label.setObjectName("sectionLabel")
        self.bowling_pad = NumberPad("bowling")
        bowling_layout.addWidget(bowling_label)
        bowling_layout.addWidget(self.bowling_pad)

        pads_layout.addLayout(batting_layout)
        pads_layout.addLayout(bowling_layout)

        controls_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Resume")
        self.undo_button = QPushButton("Undo Ball")
        self.reset_button = QPushButton("Reset Innings")
        for button in [self.start_button, self.pause_button, self.resume_button, self.undo_button, self.reset_button]:
            controls_layout.addWidget(button)

        self.highlight_badge = QLabel("LIVE")
        self.highlight_badge.setObjectName("highlightBadge")
        self.history_panel = QTextEdit()
        self.history_panel.setReadOnly(True)
        self.history_panel.setObjectName("historyPanel")

        root_layout.addWidget(title)
        root_layout.addWidget(self.summary_label)
        root_layout.addLayout(scoreboard)
        root_layout.addLayout(pads_layout)
        root_layout.addLayout(controls_layout)
        root_layout.addWidget(self.highlight_badge)
        root_layout.addWidget(self.history_panel, 1)

        self.batting_pad.number_selected.connect(self._try_submit_ball)
        self.bowling_pad.number_selected.connect(self._try_submit_ball)
        self.start_button.clicked.connect(self.controller.start_match)
        self.pause_button.clicked.connect(self.controller.pause_match)
        self.resume_button.clicked.connect(self.controller.resume_match)
        self.undo_button.clicked.connect(self.controller.undo_last_ball)
        self.reset_button.clicked.connect(self.controller.reset_current_innings)

        self.controller.state_changed.connect(self.update_snapshot)
        self.controller.highlight_changed.connect(self.show_highlight)
        self.controller.activity_logged.connect(self.append_history)
        self.controller.error_changed.connect(self.append_history)

    def update_snapshot(self, snapshot: dict) -> None:
        self.score_card.set_value(f"{snapshot['score']}/{snapshot['wickets']}")
        self.overs_card.set_value(snapshot["overs"])
        self.target_card.set_value(str(snapshot["target"] or "-"))
        self.rr_card.set_value(f"{snapshot['required_run_rate']:.2f}")
        self.summary_label.setText(
            f"{snapshot['batting_team_name']} batting against {snapshot['bowling_team_name']} | "
            f"Status: {snapshot['status'].upper()}"
        )
        if snapshot.get("result_text"):
            self.append_history(snapshot["result_text"])

    def append_history(self, message: str) -> None:
        self.history_panel.insertPlainText(f"{message}\n")
        self.history_panel.verticalScrollBar().setValue(self.history_panel.verticalScrollBar().maximum())

    def show_highlight(self, label: str) -> None:
        self.highlight_badge.setText(label)
        animation = QPropertyAnimation(self, b"pulseOpacity")
        animation.setDuration(500)
        animation.setStartValue(0.2)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        animation.start()
        self._animation = animation
        QTimer.singleShot(1200, lambda: self.highlight_badge.setText("LIVE"))

    def _try_submit_ball(self, _number: int) -> None:
        if self.batting_pad.selected_number and self.bowling_pad.selected_number:
            self.controller.submit_ball(self.batting_pad.selected_number, self.bowling_pad.selected_number)
            self.batting_pad.clear_selection()
            self.bowling_pad.clear_selection()

    def get_pulse_opacity(self) -> float:
        return self.highlight_badge.windowOpacity()

    def set_pulse_opacity(self, value: float) -> None:
        self.highlight_badge.setWindowOpacity(value)

    pulseOpacity = Property(float, get_pulse_opacity, set_pulse_opacity)
