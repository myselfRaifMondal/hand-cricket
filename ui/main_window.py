"""Main application window with sidebar navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from controllers.analytics_controller import AnalyticsController
from controllers.match_controller import MatchController
from ui.analytics_screen import AnalyticsScreen
from ui.dashboard import DashboardScreen
from ui.match_screen import MatchScreen
from ui.player_management import PlayerManagementScreen
from ui.dialogs.match_setup_dialog import MatchSetupDialog

if TYPE_CHECKING:
    from controllers.player_controller import PlayerController


class MainWindow(QMainWindow):
    """Primary desktop shell for the Hand Cricket application."""

    def __init__(
        self,
        match_controller: MatchController,
        player_controller: "PlayerController | None" = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Hand Cricket Match Management")
        self.resize(1400, 860)

        self.match_controller = match_controller
        self._analytics_controller = AnalyticsController()
        self.dashboard_screen = DashboardScreen()
        self.match_screen = MatchScreen(match_controller)
        self.analytics_screen = AnalyticsScreen()
        self.player_management_screen = PlayerManagementScreen(player_controller)

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

        self.sidebar.currentRowChanged.connect(self._on_nav_change)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack, 1)
        self.setCentralWidget(central_widget)
        QTimer.singleShot(0, self.launch_match_setup)

    _ANALYTICS_INDEX = 2

    def _on_nav_change(self, index: int) -> None:
        self.content_stack.setCurrentIndex(index)
        if index == self._ANALYTICS_INDEX:
            try:
                snapshot = self.match_controller.snapshot()
                chart_data = self._analytics_controller.build_chart_data(snapshot)
                self.analytics_screen.update_charts(chart_data)
            except Exception:  # noqa: BLE001
                pass

    def launch_match_setup(self) -> None:
        """Open mandatory pre-match setup and configure the live controller."""

        dialog = MatchSetupDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Setup Required",
                "Match setup was cancelled. You can start setup from Live Match controls by restarting the app.",
            )
            return
        try:
            self.match_controller.configure_match(dialog.payload())
            self.match_controller.activity_logged.emit("Setup completed: teams, toss, lineup, and opening players set.")
        except ValueError as error:
            QMessageBox.critical(self, "Setup Error", str(error))
