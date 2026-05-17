"""Dashboard screen with high-level live match metrics."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QListWidget, QVBoxLayout, QWidget

from ui.widgets.stat_card import StatCard


class DashboardScreen(QWidget):
    """Landing dashboard for live metrics and recent activity."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("Live Command Center")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Recent match state, chase pressure, and live event feed.")
        subtitle.setObjectName("screenSubtitle")

        stats_layout = QGridLayout()
        stats_layout.setSpacing(16)
        self.score_card = StatCard("Current Score", "0/0", "score")
        self.overs_card = StatCard("Overs", "0.0", "muted")
        self.rr_card = StatCard("Current RR", "0.00", "accent")
        self.target_card = StatCard("Target", "0", "accent")

        stats_layout.addWidget(self.score_card, 0, 0)
        stats_layout.addWidget(self.overs_card, 0, 1)
        stats_layout.addWidget(self.rr_card, 1, 0)
        stats_layout.addWidget(self.target_card, 1, 1)

        self.activity_list = QListWidget()
        self.activity_list.setObjectName("activityList")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(stats_layout)
        layout.addWidget(self.activity_list, 1)

    def update_snapshot(self, snapshot: dict) -> None:
        self.score_card.set_value(f"{snapshot['score']}/{snapshot['wickets']}")
        self.overs_card.set_value(snapshot["overs"])
        self.rr_card.set_value(f"{snapshot['current_run_rate']:.2f}")
        self.target_card.set_value(str(snapshot["target"] or "-"))

    def add_activity(self, message: str) -> None:
        self.activity_list.insertItem(0, message)
