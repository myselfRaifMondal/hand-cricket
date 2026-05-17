"""Application bootstrap for the Hand Cricket desktop software."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from controllers.match_controller import MatchController
from database.db import initialize_database
from ui.main_window import MainWindow
from utils.helpers import ensure_runtime_directories, load_settings, safe_read_text
from utils.logger import configure_logging


def main() -> int:
    """Start the desktop application."""

    settings = load_settings()
    ensure_runtime_directories(settings)
    logger = configure_logging(settings)
    initialize_database(settings)

    app = QApplication(sys.argv)
    app.setApplicationName(settings.application_name)
    app.setStyleSheet(safe_read_text(settings.theme_path))

    match_controller = MatchController()
    window = MainWindow(match_controller)
    window.show()

    logger.info("Application started successfully")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
