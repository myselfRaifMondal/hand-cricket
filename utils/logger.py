"""Logging setup for the desktop application."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from utils.helpers import AppSettings


def configure_logging(settings: AppSettings) -> logging.Logger:
    """Configure application logging with console and rotating file handlers."""

    logger = logging.getLogger("hand_cricket")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        settings.log_path,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
