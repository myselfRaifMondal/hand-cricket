"""Validation helpers for runtime and UI input."""

from __future__ import annotations

from utils.constants import ALLOWED_HAND_NUMBERS


def validate_hand_number(number: int) -> None:
    """Ensure the selected hand number is valid."""

    if number not in ALLOWED_HAND_NUMBERS:
        raise ValueError(f"Hand number must be in {ALLOWED_HAND_NUMBERS}.")


def validate_match_configuration(overs: int, innings: int, max_wickets: int) -> None:
    """Validate basic match configuration values."""

    if overs <= 0:
        raise ValueError("Overs must be greater than zero.")
    if innings < 2:
        raise ValueError("At least two innings are required.")
    if max_wickets <= 0:
        raise ValueError("Max wickets must be greater than zero.")
