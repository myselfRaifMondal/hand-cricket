"""Initial analytics screen with textual summary placeholders backed by live data."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class AnalyticsScreen(QWidget):
    """Initial analytics view to be expanded with chart rendering."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        title = QLabel("Analytics Workspace")
        title.setObjectName("screenTitle")
        subtitle = QLabel("The first slice exposes live summary data; charts land in the next phase.")
        subtitle.setObjectName("screenSubtitle")
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setText(
            "Worm graph, Manhattan chart, partnership analysis, and win probability will be generated "
            "from ball events and embedded here."
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.summary, 1)
