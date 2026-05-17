"""Application-wide constants and enums."""

from __future__ import annotations

from enum import StrEnum

APP_NAME = "Hand Cricket Match Management"
APP_ORGANIZATION = "OpenScore Labs"
ALLOWED_HAND_NUMBERS = (1, 2, 3, 4, 5, 6)
BALLS_PER_OVER = 6


class MatchStatus(StrEnum):
    DRAFT = "draft"
    LIVE = "live"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InningsStatus(StrEnum):
    PENDING = "pending"
    LIVE = "live"
    COMPLETED = "completed"


class TossDecision(StrEnum):
    BAT = "bat"
    BOWL = "bowl"


class PlayerRole(StrEnum):
    BATTER = "batter"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    WICKET_KEEPER = "wicket_keeper"


class AnimationEvent(StrEnum):
    OUT = "OUT"
    FOUR = "FOUR"
    SIX = "SIX"
    WICKET = "WICKET"
    WINNER = "WINNER"
    RUN = "RUN"


DEFAULT_SETTINGS = {
    "application_name": APP_NAME,
    "database_path": "data/hand_cricket.sqlite3",
    "log_path": "logs/application.log",
    "analytics_cache_path": "data/cache",
    "theme_path": "ui/themes/dark.qss",
    "sqlalchemy_echo": False,
    "default_overs": 5,
    "default_innings": 2,
    "enable_super_over": True,
}
