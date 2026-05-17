"""Helper utilities for settings, formatting, and filesystem concerns."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.constants import APP_NAME, BALLS_PER_OVER, DEFAULT_SETTINGS


def project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class AppSettings:
    """Runtime settings loaded from JSON configuration."""

    application_name: str = APP_NAME
    database_path: Path = project_root() / "data/hand_cricket.sqlite3"
    log_path: Path = project_root() / "logs/application.log"
    analytics_cache_path: Path = project_root() / "data/cache"
    theme_path: Path = project_root() / "ui/themes/dark.qss"
    sqlalchemy_echo: bool = False
    default_overs: int = 5
    default_innings: int = 2
    enable_super_over: bool = True

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "AppSettings":
        root = project_root()
        merged = {**DEFAULT_SETTINGS, **mapping}
        return cls(
            application_name=merged["application_name"],
            database_path=root / merged["database_path"],
            log_path=root / merged["log_path"],
            analytics_cache_path=root / merged["analytics_cache_path"],
            theme_path=root / merged["theme_path"],
            sqlalchemy_echo=bool(merged["sqlalchemy_echo"]),
            default_overs=int(merged["default_overs"]),
            default_innings=int(merged["default_innings"]),
            enable_super_over=bool(merged["enable_super_over"]),
        )


def load_settings(config_path: Path | None = None) -> AppSettings:
    """Load JSON settings, falling back to defaults."""

    path = config_path or project_root() / "config/settings.json"
    if not path.exists():
        return AppSettings.from_mapping({})
    with path.open("r", encoding="utf-8") as file_handle:
        return AppSettings.from_mapping(json.load(file_handle))


def ensure_runtime_directories(settings: AppSettings) -> None:
    """Ensure data, log, and cache directories exist before startup."""

    for path in [
        settings.database_path.parent,
        settings.log_path.parent,
        settings.analytics_cache_path,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def balls_to_overs(balls_bowled: int) -> str:
    """Format balls bowled as cricket over notation."""

    return f"{balls_bowled // BALLS_PER_OVER}.{balls_bowled % BALLS_PER_OVER}"


def safe_read_text(path: Path) -> str:
    """Read a text file if present; otherwise return an empty string."""

    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
