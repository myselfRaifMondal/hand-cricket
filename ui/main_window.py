"""Main application window with sidebar navigation."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QWidget

from controllers.match_controller import MatchController
from ui.analytics_screen import AnalyticsScreen
from ui.dashboard import DashboardScreen
from ui.match_screen import MatchScreen
from ui.player_management import PlayerManagementScreen


class MainWindow(QMainWindow):
    """Primary desktop shell for the Hand Cricket application."""

    def __init__(self, match_controller: MatchController) -> None:
        super().__init__()
        self.setWindowTitle("Hand Cricket Match Management")
        self.resize(1400, 860)

        self.match_controller = match_controller
        self.dashboard_screen = DashboardScreen()
        self.match_screen = MatchScreen(match_controller)
        self.analytics_screen = AnalyticsScreen()
        self.player_management_screen = PlayerManagementScreen()

        self.match_controller.state_changed.connect(self.dashboard_screen.update_snapshot)
        self.match_controller.activity_logged.connect(self.dashboard_screen.add_activity)

        central_widget = QWidget()
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        for label in ["Dashboard", "Live Match", "Analytics", "Players"]:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sidebar.addItem(item)
        self.sidebar.setCurrentRow(0)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.dashboard_screen)
        self.content_stack.addWidget(self.match_screen)
        self.content_stack.addWidget(self.analytics_screen)
        self.content_stack.addWidget(self.player_management_screen)

        self.sidebar.currentRowChanged.connect(self.content_stack.setCurrentIndex)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack, 1)
        self.setCentralWidget(central_widget)
