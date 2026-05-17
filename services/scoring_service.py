"""Application-facing scoring service built on top of the pure match engine."""

from __future__ import annotations

from typing import Any, Optional

from services.match_engine import MatchConfig, MatchEngine, MatchState


class ScoringService:
    """Coordinates match setup and ball-by-ball updates for the UI layer."""

    def __init__(self, engine: MatchEngine | None = None) -> None:
        self.engine = engine or MatchEngine()
        self.state: MatchState | None = None

    def create_match(self, config: MatchConfig) -> MatchState:
        self.state = self.engine.create_match(config)
        return self.state

    def start_match(self) -> MatchState:
        state = self._require_state()
        return self.engine.start_match(state)

    def pause_match(self) -> MatchState:
        state = self._require_state()
        return self.engine.pause_match(state)

    def resume_match(self) -> MatchState:
        state = self._require_state()
        return self.engine.resume_match(state)

    def reset_current_innings(self) -> MatchState:
        state = self._require_state()
        return self.engine.reset_current_innings(state)

    def record_ball(
        self,
        batting_input: int,
        bowling_input: int,
        batter_name: Optional[str] = None,
        bowler_name: Optional[str] = None,
    ) -> dict[str, Any]:
        state = self._require_state()
        event = self.engine.record_ball(state, batting_input, bowling_input, batter_name, bowler_name)
        return {"event": event, "snapshot": self.engine.get_snapshot(state)}

    def undo_last_ball(self) -> dict[str, Any]:
        state = self._require_state()
        event = self.engine.undo_last_ball(state)
        return {"event": event, "snapshot": self.engine.get_snapshot(state)}

    def snapshot(self) -> dict[str, Any]:
        return self.engine.get_snapshot(self._require_state())

    def _require_state(self) -> MatchState:
        if self.state is None:
            raise ValueError("A match has not been created yet.")
        return self.state
