"""Qt controller that exposes live match actions and signals."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from services.match_engine import MatchConfig, MatchEngine, MatchState, TeamConfig
from services.scoring_service import ScoringService
from utils.constants import AnimationEvent


class MatchController(QObject):
    """Controller for match setup and live score updates."""

    state_changed = Signal(dict)
    highlight_changed = Signal(str)
    error_changed = Signal(str)
    activity_logged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.service = ScoringService(MatchEngine())
        self.team_name_by_id: dict[int, str] = {}
        self.create_demo_match()

    def create_demo_match(self) -> MatchState:
        config = MatchConfig(
            home_team=TeamConfig(team_id=1, name="Falcons"),
            away_team=TeamConfig(team_id=2, name="Titans"),
            batting_first_team_id=1,
            bowling_first_team_id=2,
            overs=5,
            innings_count=2,
            max_wickets=5,
        )
        self.team_name_by_id = {1: "Falcons", 2: "Titans"}
        state = self.service.create_match(config)
        self._emit_state()
        return state

    def start_match(self) -> None:
        try:
            self.service.start_match()
            self.activity_logged.emit("Match started")
            self._emit_state()
        except ValueError as error:
            self.error_changed.emit(str(error))

    def pause_match(self) -> None:
        try:
            self.service.pause_match()
            self.activity_logged.emit("Match paused")
            self._emit_state()
        except ValueError as error:
            self.error_changed.emit(str(error))

    def resume_match(self) -> None:
        try:
            self.service.resume_match()
            self.activity_logged.emit("Match resumed")
            self._emit_state()
        except ValueError as error:
            self.error_changed.emit(str(error))

    def reset_current_innings(self) -> None:
        try:
            self.service.reset_current_innings()
            self.activity_logged.emit("Current innings reset")
            self._emit_state()
        except ValueError as error:
            self.error_changed.emit(str(error))

    def undo_last_ball(self) -> None:
        try:
            result = self.service.undo_last_ball()
            event = result["event"]
            self.activity_logged.emit(
                f"Undid ball {event.over_notation} from innings {event.innings_number}"
            )
            self._emit_state()
        except ValueError as error:
            self.error_changed.emit(str(error))

    def submit_ball(self, batting_input: int, bowling_input: int) -> None:
        try:
            result = self.service.record_ball(batting_input, bowling_input)
            event = result["event"]
            highlight = self._highlight_for_event(event.runs_scored, event.is_wicket, result["snapshot"])
            self.highlight_changed.emit(highlight.value)
            self.activity_logged.emit(
                f"Innings {event.innings_number} {event.over_notation}: {event.runs_scored} runs"
                if not event.is_wicket
                else f"Innings {event.innings_number} {event.over_notation}: wicket"
            )
            self._emit_state(result["snapshot"])
        except ValueError as error:
            self.error_changed.emit(str(error))

    def snapshot(self) -> dict:
        snapshot = self.service.snapshot()
        return self._decorate_snapshot(snapshot)

    def _emit_state(self, snapshot: dict | None = None) -> None:
        state_snapshot = self._decorate_snapshot(snapshot or self.service.snapshot())
        self.state_changed.emit(state_snapshot)

    def _decorate_snapshot(self, snapshot: dict) -> dict:
        snapshot = {**snapshot}
        snapshot["batting_team_name"] = self.team_name_by_id.get(snapshot["batting_team_id"], "Unknown")
        snapshot["bowling_team_name"] = self.team_name_by_id.get(snapshot["bowling_team_id"], "Unknown")
        if snapshot["winner_team_id"]:
            snapshot["winner_team_name"] = self.team_name_by_id.get(snapshot["winner_team_id"], "Unknown")
        return snapshot

    def _highlight_for_event(self, runs_scored: int, is_wicket: bool, snapshot: dict) -> AnimationEvent:
        if snapshot.get("winner_team_id"):
            return AnimationEvent.WINNER
        if is_wicket:
            return AnimationEvent.OUT
        if runs_scored == 6:
            return AnimationEvent.SIX
        if runs_scored == 4:
            return AnimationEvent.FOUR
        return AnimationEvent.RUN
