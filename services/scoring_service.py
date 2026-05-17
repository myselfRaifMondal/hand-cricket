"""Application-facing scoring service built on top of the pure match engine."""

from __future__ import annotations

from typing import Any, Optional

from services.match_engine import MatchConfig, MatchEngine, MatchState
from utils.helpers import AppSettings


class ScoringService:
    """Coordinates match setup and ball-by-ball updates for the UI layer.

    Pass *settings* to enable SQLite persistence; omit for pure in-memory use.
    """

    def __init__(
        self,
        engine: MatchEngine | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        self.engine = engine or MatchEngine()
        self.state: MatchState | None = None
        self._settings = settings
        self._repo: Any = None  # MatchRepository, imported lazily to avoid circular imports
        self._db_match_id: int | None = None
        self._db_team_id_map: dict[int, int] = {}   # in-memory team_id → DB team_id
        self._db_innings_id_map: dict[int, int] = {}  # innings_number → DB innings_id

        if settings is not None:
            from database.match_repository import MatchRepository  # noqa: PLC0415
            self._repo = MatchRepository(settings)

    def create_match(self, config: MatchConfig) -> MatchState:
        self.state = self.engine.create_match(config)
        self._db_match_id = None
        self._db_team_id_map = {}
        self._db_innings_id_map = {}
        if self._repo is not None:
            home_name = config.home_team.name
            away_name = config.away_team.name
            batting_first = config.home_team.name if config.batting_first_team_id == config.home_team.team_id else config.away_team.name
            bowling_first = config.away_team.name if batting_first == home_name else home_name
            match_id, home_db_id, away_db_id = self._repo.create_match(
                home_name=home_name,
                away_name=away_name,
                batting_first_name=batting_first,
                bowling_first_name=bowling_first,
                overs=config.overs,
                innings_count=config.innings_count,
            )
            self._db_match_id = match_id
            self._db_team_id_map[config.home_team.team_id] = home_db_id
            self._db_team_id_map[config.away_team.team_id] = away_db_id
        return self.state

    def start_match(self) -> MatchState:
        state = self._require_state()
        self.engine.start_match(state)
        if self._repo is not None and self._db_match_id is not None:
            self._repo.mark_match_live(self._db_match_id)
        return state

    def pause_match(self) -> MatchState:
        state = self._require_state()
        return self.engine.pause_match(state)

    def resume_match(self) -> MatchState:
        state = self._require_state()
        return self.engine.resume_match(state)

    def reset_current_innings(self) -> MatchState:
        state = self._require_state()
        innings_before = state.current_innings()
        innings_number = innings_before.innings_number
        innings_id = self._db_innings_id_map.get(innings_number)
        self.engine.reset_current_innings(state)
        if self._repo is not None and innings_id is not None:
            self._repo.delete_all_balls(innings_id)
        return state

    def record_ball(
        self,
        batting_input: int,
        bowling_input: int,
        batter_name: Optional[str] = None,
        bowler_name: Optional[str] = None,
    ) -> dict[str, Any]:
        state = self._require_state()
        innings_before_completed = state.current_innings().completed
        innings_number_before = state.current_innings().innings_number

        event = self.engine.record_ball(state, batting_input, bowling_input, batter_name, bowler_name)
        snapshot = self.engine.get_snapshot(state)

        if self._repo is not None and self._db_match_id is not None:
            innings = state.innings[innings_number_before - 1]
            innings_id = self._ensure_db_innings(state, innings_number_before)
            over_number = (event.sequence_number - 1) // 6
            ball_in_over = (event.sequence_number - 1) % 6
            self._repo.append_ball(
                innings_id=innings_id,
                sequence_number=event.sequence_number,
                over_number=over_number,
                ball_in_over=ball_in_over,
                batting_input=event.batting_input,
                bowling_input=event.bowling_input,
                runs_scored=event.runs_scored,
                is_wicket=event.is_wicket,
            )
            # If that ball completed the innings, persist the final totals
            if not innings_before_completed and innings.completed:
                self._repo.complete_innings(
                    innings_id=innings_id,
                    runs=innings.runs,
                    wickets=innings.wickets,
                    balls_bowled=innings.balls_bowled,
                )
            # If the full match completed, mark it done
            if snapshot.get("status") == "completed" and self._db_match_id is not None:
                self._repo.complete_match(
                    match_id=self._db_match_id,
                    winner_team_id=self._db_team_id_map.get(state.winner_team_id or 0),
                    result_summary=state.result_text,
                )

        return {"event": event, "snapshot": snapshot}

    def undo_last_ball(self) -> dict[str, Any]:
        state = self._require_state()
        # Capture the current innings number before undo rewrites state
        innings_number = state.current_innings().innings_number
        innings_was_completed = state.current_innings().completed

        event = self.engine.undo_last_ball(state)
        snapshot = self.engine.get_snapshot(state)

        if self._repo is not None:
            # The event's innings_number tells us which innings the undone ball belonged to
            undone_innings_number = event.innings_number
            innings_id = self._db_innings_id_map.get(undone_innings_number)
            if innings_id is not None:
                self._repo.delete_last_ball(innings_id)

        return {"event": event, "snapshot": snapshot}

    def snapshot(self) -> dict[str, Any]:
        return self.engine.get_snapshot(self._require_state())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_state(self) -> MatchState:
        if self.state is None:
            raise ValueError("A match has not been created yet.")
        return self.state

    def _ensure_db_innings(self, state: MatchState, innings_number: int) -> int:
        """Return the DB innings_id, creating the Innings row if needed."""

        if innings_number in self._db_innings_id_map:
            return self._db_innings_id_map[innings_number]

        innings = state.innings[innings_number - 1]
        batting_db_id = self._db_team_id_map.get(innings.batting_team_id, innings.batting_team_id)
        bowling_db_id = self._db_team_id_map.get(innings.bowling_team_id, innings.bowling_team_id)
        innings_id = self._repo.ensure_innings(
            match_id=self._db_match_id,  # type: ignore[arg-type]
            innings_number=innings_number,
            batting_team_id=batting_db_id,
            bowling_team_id=bowling_db_id,
            target_runs=innings.target,
        )
        self._db_innings_id_map[innings_number] = innings_id
        return innings_id
