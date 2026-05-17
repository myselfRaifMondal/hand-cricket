"""Initial team and player management surface."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class PlayerManagementScreen(QWidget):
    """Basic roster table used as the starting point for player CRUD."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        title = QLabel("Team And Player Management")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Roster editing will be connected to SQLite-backed CRUD in the next slice.")
        subtitle.setObjectName("screenSubtitle")

        self.table = QTableWidget(4, 4)
        self.table.setHorizontalHeaderLabels(["Team", "Player", "Role", "Jersey"])
        sample_rows = [
            ("Falcons", "A. Ray", "All-Rounder", "7"),
            ("Falcons", "K. Sen", "Bowler", "18"),
            ("Titans", "R. Das", "Batter", "10"),
            ("Titans", "J. Ali", "All-Rounder", "23"),
        ]
        for row_index, row in enumerate(sample_rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.table, 1)
