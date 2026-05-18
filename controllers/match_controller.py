"""Qt controller that exposes live match actions and signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QObject, Signal

from services.match_engine import MatchConfig, MatchEngine, MatchState, TeamConfig
from services.scoring_service import ScoringService
from utils.constants import AnimationEvent
from utils.helpers import AppSettings


class MatchController(QObject):
    """Controller for match setup and live score updates."""

    state_changed = Signal(dict)
    highlight_changed = Signal(str)
    error_changed = Signal(str)
    activity_logged = Signal(str)

    def __init__(self, settings: Optional[AppSettings] = None) -> None:
        super().__init__()
        self.service = ScoringService(MatchEngine(), settings=settings)
        self.team_name_by_id: dict[int, str] = {}
        self._batting_orders: dict[int, list[str]] = {}
        self._current_striker: str | None = None
        self._current_bowler: str | None = None
        self._needs_next_batter = False
        self._needs_next_bowler = False
        self._last_innings_number: int | None = None
        self._dismissed_innings_batters: dict[int, list[str]] = {}

    @dataclass(slots=True)
    class SetupPayload:
        home_team_name: str
        away_team_name: str
        overs: int
        max_wickets: int
        toss_winner_name: str
        toss_decision: str
        home_batting_order: list[str]
        away_batting_order: list[str]
        opening_striker: str
        opening_bowler: str

    def _validate_setup_payload(self, payload: SetupPayload, batting_first_team_id: int) -> None:
        required_players = payload.max_wickets + 1
        if len(payload.home_batting_order) < required_players:
            raise ValueError(
                f"Home lineup must include at least {required_players} players for {payload.max_wickets} wickets."
            )
        if len(payload.away_batting_order) < required_players:
            raise ValueError(
                f"Away lineup must include at least {required_players} players for {payload.max_wickets} wickets."
            )

        batting_lineup = payload.home_batting_order if batting_first_team_id == 1 else payload.away_batting_order
        bowling_lineup = payload.away_batting_order if batting_first_team_id == 1 else payload.home_batting_order
        if payload.opening_striker not in batting_lineup:
            raise ValueError("Opening batter must belong to the team batting first.")
        if payload.opening_bowler not in bowling_lineup:
            raise ValueError("Opening bowler must belong to the bowling team.")

    def configure_match(self, payload: SetupPayload) -> MatchState:
        batting_first_home = (payload.toss_winner_name == payload.home_team_name and payload.toss_decision == "bat") or (
            payload.toss_winner_name == payload.away_team_name and payload.toss_decision == "bowl"
        )
        batting_first_team_id = 1 if batting_first_home else 2
        bowling_first_team_id = 2 if batting_first_home else 1
        self._validate_setup_payload(payload, batting_first_team_id)

        config = MatchConfig(
            home_team=TeamConfig(team_id=1, name=payload.home_team_name),
            away_team=TeamConfig(team_id=2, name=payload.away_team_name),
            batting_first_team_id=batting_first_team_id,
            bowling_first_team_id=bowling_first_team_id,
            overs=payload.overs,
            innings_count=2,
            max_wickets=payload.max_wickets,
        )
        state = self.service.create_match(config)
        self.team_name_by_id = {1: payload.home_team_name, 2: payload.away_team_name}
        self._batting_orders = {
            1: list(payload.home_batting_order),
            2: list(payload.away_batting_order),
        }
        self._dismissed_innings_batters = {1: [], 2: []}
        self._current_striker = payload.opening_striker
        self._current_bowler = payload.opening_bowler
        self._needs_next_batter = False
        self._needs_next_bowler = False
        self._last_innings_number = state.current_innings().innings_number
        self._emit_state()
        self.activity_logged.emit("Match configured. Ready to start.")
        return state

    def is_configured(self) -> bool:
        return self.service.state is not None

    def next_batter_options(self) -> list[str]:
        state = self.service.state
        if state is None:
            return []
        innings = state.current_innings()
        team_id = innings.batting_team_id
        lineup = self._batting_orders.get(team_id, [])
        dismissed = set(self._dismissed_innings_batters.get(innings.innings_number, []))
        unavailable = dismissed | {name for name in [self._current_striker] if name}
        return [name for name in lineup if name not in unavailable]

    def next_bowler_options(self) -> list[str]:
        state = self.service.state
        if state is None:
            return []
        bowling_team_id = state.current_innings().bowling_team_id
        lineup = self._batting_orders.get(bowling_team_id, [])
        return list(lineup)

    def select_next_batter(self, batter_name: str) -> None:
        self._current_striker = batter_name
        self._needs_next_batter = False
        self.activity_logged.emit(f"Next batter in: {batter_name}")
        self._emit_state()

    def select_next_bowler(self, bowler_name: str) -> None:
        self._current_bowler = bowler_name
        self._needs_next_bowler = False
        self.activity_logged.emit(f"New bowler: {bowler_name}")
        self._emit_state()

    def start_match(self) -> None:
        try:
            if not self.is_configured():
                raise ValueError("Please complete match setup first.")
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
            if self._needs_next_batter:
                raise ValueError("Select the next batter before recording another ball.")
            if self._needs_next_bowler:
                raise ValueError("Select the next bowler before recording another ball.")
            if not self._current_striker or not self._current_bowler:
                raise ValueError("Current striker and bowler must be selected.")

            innings_before = self.service.state.current_innings().innings_number if self.service.state else 1
            result = self.service.record_ball(
                batting_input,
                bowling_input,
                batter_name=self._current_striker,
                bowler_name=self._current_bowler,
            )
            event = result["event"]
            highlight = self._highlight_for_event(event.runs_scored, event.is_wicket, result["snapshot"])
            self.highlight_changed.emit(highlight.value)
            if event.is_wicket and self._current_striker:
                dismissed = self._dismissed_innings_batters.setdefault(event.innings_number, [])
                dismissed.append(self._current_striker)
                self._needs_next_batter = True
                if not self.next_batter_options():
                    result = self.service.complete_current_innings()
                    self._needs_next_batter = False
                    self.activity_logged.emit("No available next batter in lineup. Innings closed.")
            if event.sequence_number % 6 == 0 and result["snapshot"].get("status") == "live":
                self._needs_next_bowler = True

            innings_after = result["snapshot"].get("current_innings")
            if innings_after != innings_before and result["snapshot"].get("status") == "live":
                # Start of a new innings: auto-prime opening batters from lineup and ask for opening bowler.
                team_id = int(result["snapshot"]["batting_team_id"])
                lineup = self._batting_orders.get(team_id, [])
                if lineup:
                    self._current_striker = lineup[0]
                self._dismissed_innings_batters.setdefault(int(innings_after), [])
                self._needs_next_batter = False
                self._needs_next_bowler = True

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
        snapshot["current_striker"] = self._current_striker or "-"
        snapshot["current_bowler"] = self._current_bowler or "-"
        snapshot["needs_next_batter"] = self._needs_next_batter
        snapshot["needs_next_bowler"] = self._needs_next_bowler
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
