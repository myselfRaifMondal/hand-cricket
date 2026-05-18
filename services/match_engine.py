"""Pure hand cricket match engine used by controllers and services."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from utils.constants import BALLS_PER_OVER, MatchStatus
from utils.helpers import balls_to_overs
from utils.validators import validate_hand_number, validate_match_configuration


@dataclass(slots=True)
class TeamConfig:
    """Configuration for a participating team."""

    team_id: int
    name: str


@dataclass(slots=True)
class MatchConfig:
    """Configuration used to initialize a match."""

    home_team: TeamConfig
    away_team: TeamConfig
    batting_first_team_id: int
    bowling_first_team_id: int
    overs: int
    innings_count: int = 2
    max_wickets: int = 5
    allow_super_over: bool = True
    super_over_overs: int = 1
    super_over_max_wickets: int = 2

    def __post_init__(self) -> None:
        validate_match_configuration(self.overs, self.innings_count, self.max_wickets)
        if self.batting_first_team_id == self.bowling_first_team_id:
            raise ValueError("Batting and bowling teams must be different.")


@dataclass(slots=True)
class BallEvent:
    """Immutable description of a recorded delivery."""

    innings_number: int
    sequence_number: int
    batting_input: int
    bowling_input: int
    runs_scored: int
    is_wicket: bool
    total_score_after: int
    wickets_after: int
    over_notation: str
    batter_name: Optional[str] = None
    bowler_name: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class InningsState:
    """Mutable innings state that can be reconstructed from ball history."""

    innings_number: int
    batting_team_id: int
    bowling_team_id: int
    max_overs: int
    max_wickets: int
    target: Optional[int] = None
    is_super_over: bool = False
    runs: int = 0
    wickets: int = 0
    balls_bowled: int = 0
    completed: bool = False
    history: list[BallEvent] = field(default_factory=list)

    @property
    def max_balls(self) -> int:
        return self.max_overs * BALLS_PER_OVER


@dataclass(slots=True)
class MatchState:
    """Entire match state, independent of persistence or UI."""

    config: MatchConfig
    status: MatchStatus = MatchStatus.DRAFT
    innings: list[InningsState] = field(default_factory=list)
    current_innings_index: int = 0
    winner_team_id: Optional[int] = None
    result_text: str = ""

    def current_innings(self) -> InningsState:
        return self.innings[self.current_innings_index]


class MatchEngine:
    """Applies Hand Cricket rules to a mutable match state."""

    def create_match(self, config: MatchConfig) -> MatchState:
        innings = self._build_innings_schedule(config)
        return MatchState(config=config, innings=innings)

    def start_match(self, state: MatchState) -> MatchState:
        if state.status == MatchStatus.COMPLETED:
            raise ValueError("Completed matches cannot be restarted.")
        state.status = MatchStatus.LIVE
        return state

    def pause_match(self, state: MatchState) -> MatchState:
        if state.status != MatchStatus.LIVE:
            raise ValueError("Only a live match can be paused.")
        state.status = MatchStatus.PAUSED
        return state

    def resume_match(self, state: MatchState) -> MatchState:
        if state.status != MatchStatus.PAUSED:
            raise ValueError("Only a paused match can be resumed.")
        state.status = MatchStatus.LIVE
        return state

    def end_match(self, state: MatchState, reason: str = "Ended by admin") -> MatchState:
        state.status = MatchStatus.COMPLETED
        if not state.result_text:
            state.result_text = reason
        return state

    def reset_current_innings(self, state: MatchState) -> MatchState:
        innings = state.current_innings()
        innings.history.clear()
        innings.runs = 0
        innings.wickets = 0
        innings.balls_bowled = 0
        innings.completed = False
        if state.status == MatchStatus.COMPLETED:
            state.status = MatchStatus.LIVE
            state.winner_team_id = None
            state.result_text = ""
        return state

    def complete_current_innings(self, state: MatchState) -> MatchState:
        """Mark the current innings complete and progress match state."""

        if state.status != MatchStatus.LIVE:
            raise ValueError("Only a live match innings can be completed.")
        innings = state.current_innings()
        if innings.completed:
            raise ValueError("The current innings is already completed.")
        innings.completed = True
        self._advance_match(state)
        return state

    def record_ball(
        self,
        state: MatchState,
        batting_input: int,
        bowling_input: int,
        batter_name: Optional[str] = None,
        bowler_name: Optional[str] = None,
    ) -> BallEvent:
        if state.status != MatchStatus.LIVE:
            raise ValueError("The match must be live to record a ball.")

        validate_hand_number(batting_input)
        validate_hand_number(bowling_input)

        innings = state.current_innings()
        if innings.completed:
            raise ValueError("The current innings is already completed.")

        is_wicket = batting_input == bowling_input
        runs_scored = 0 if is_wicket else batting_input
        innings.balls_bowled += 1
        innings.runs += runs_scored
        innings.wickets += 1 if is_wicket else 0

        sequence_number = len(innings.history) + 1
        over_notation = balls_to_overs(innings.balls_bowled)
        event = BallEvent(
            innings_number=innings.innings_number,
            sequence_number=sequence_number,
            batting_input=batting_input,
            bowling_input=bowling_input,
            runs_scored=runs_scored,
            is_wicket=is_wicket,
            total_score_after=innings.runs,
            wickets_after=innings.wickets,
            over_notation=over_notation,
            batter_name=batter_name,
            bowler_name=bowler_name,
        )
        innings.history.append(event)

        if self._should_complete_innings(innings):
            innings.completed = True
            self._advance_match(state)
        return event

    def undo_last_ball(self, state: MatchState) -> BallEvent:
        innings_index = self._last_innings_with_history(state)
        if innings_index is None:
            raise ValueError("There is no ball to undo.")

        if innings_index != state.current_innings_index:
            state.current_innings_index = innings_index
            state.status = MatchStatus.LIVE
            state.winner_team_id = None
            state.result_text = ""
            for following in state.innings[innings_index + 1 :]:
                following.completed = False
                following.history.clear()
                following.runs = 0
                following.wickets = 0
                following.balls_bowled = 0
                if following.innings_number == len(state.innings):
                    following.target = None

        innings = state.current_innings()
        removed_event = innings.history.pop()
        self._recalculate_innings(innings)
        state.status = MatchStatus.LIVE
        state.winner_team_id = None
        state.result_text = ""
        return removed_event

    def get_snapshot(self, state: MatchState) -> dict[str, Any]:
        innings = state.current_innings()
        team_totals = self._team_totals(state)
        target = innings.target or 0
        runs_remaining = max(target - innings.runs, 0) if target else 0
        balls_remaining = max(innings.max_balls - innings.balls_bowled, 0)
        required_run_rate = (runs_remaining / balls_remaining * BALLS_PER_OVER) if balls_remaining and target else 0.0
        current_run_rate = (innings.runs / innings.balls_bowled * BALLS_PER_OVER) if innings.balls_bowled else 0.0

        return {
            "status": state.status.value,
            "result_text": state.result_text,
            "winner_team_id": state.winner_team_id,
            "current_innings": innings.innings_number,
            "batting_team_id": innings.batting_team_id,
            "bowling_team_id": innings.bowling_team_id,
            "score": innings.runs,
            "wickets": innings.wickets,
            "overs": balls_to_overs(innings.balls_bowled),
            "balls_remaining": balls_remaining,
            "target": target,
            "current_run_rate": round(current_run_rate, 2),
            "required_run_rate": round(required_run_rate, 2),
            "team_totals": team_totals,
            "history": [asdict(event) for event in innings.history],
        }

    def _build_innings_schedule(self, config: MatchConfig) -> list[InningsState]:
        innings: list[InningsState] = []
        batting_team_id = config.batting_first_team_id
        bowling_team_id = config.bowling_first_team_id
        for innings_number in range(1, config.innings_count + 1):
            innings.append(
                InningsState(
                    innings_number=innings_number,
                    batting_team_id=batting_team_id,
                    bowling_team_id=bowling_team_id,
                    max_overs=config.overs,
                    max_wickets=config.max_wickets,
                )
            )
            batting_team_id, bowling_team_id = bowling_team_id, batting_team_id
        return innings

    def _should_complete_innings(self, innings: InningsState) -> bool:
        if innings.wickets >= innings.max_wickets:
            return True
        if innings.balls_bowled >= innings.max_balls:
            return True
        if innings.target is not None and innings.runs >= innings.target:
            return True
        return False

    def _advance_match(self, state: MatchState) -> None:
        current_innings = state.current_innings()
        if current_innings.target is not None and current_innings.runs >= current_innings.target:
            state.status = MatchStatus.COMPLETED
            state.winner_team_id = current_innings.batting_team_id
            margin = current_innings.max_wickets - current_innings.wickets
            state.result_text = f"Team {current_innings.batting_team_id} won by {margin} wickets"
            return

        if state.current_innings_index < len(state.innings) - 1:
            state.current_innings_index += 1
            next_innings = state.current_innings()
            next_innings.target = self._determine_target_for_innings(state, next_innings.innings_number)
            state.status = MatchStatus.LIVE
            return

        winner_team_id, result_text = self._resolve_match_result(state)
        if winner_team_id is None and state.config.allow_super_over:
            self._append_super_over_pair(state)
            state.current_innings_index += 1
            state.status = MatchStatus.LIVE
            return

        state.status = MatchStatus.COMPLETED
        state.winner_team_id = winner_team_id
        state.result_text = result_text

    def _determine_target_for_innings(self, state: MatchState, innings_number: int) -> Optional[int]:
        if innings_number != len(state.innings):
            return None
        totals = self._team_totals(state)
        batting_team_id = state.current_innings().batting_team_id
        opponent_total = max(total for team_id, total in totals.items() if team_id != batting_team_id)
        return opponent_total + 1

    def _resolve_match_result(self, state: MatchState) -> tuple[Optional[int], str]:
        totals = self._team_totals(state)
        ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        if len(ranked) < 2 or ranked[0][1] == ranked[1][1]:
            return None, "Match tied"
        winner_team_id, winner_total = ranked[0]
        runner_up_total = ranked[1][1]
        return winner_team_id, f"Team {winner_team_id} won by {winner_total - runner_up_total} runs"

    def _append_super_over_pair(self, state: MatchState) -> None:
        batting_first = state.config.batting_first_team_id
        bowling_first = state.config.bowling_first_team_id
        start_number = len(state.innings) + 1
        for offset, pair in enumerate([(batting_first, bowling_first), (bowling_first, batting_first)], start=0):
            batting_team_id, bowling_team_id = pair
            state.innings.append(
                InningsState(
                    innings_number=start_number + offset,
                    batting_team_id=batting_team_id,
                    bowling_team_id=bowling_team_id,
                    max_overs=state.config.super_over_overs,
                    max_wickets=state.config.super_over_max_wickets,
                    is_super_over=True,
                )
            )

    def _team_totals(self, state: MatchState) -> dict[int, int]:
        totals: dict[int, int] = {
            state.config.home_team.team_id: 0,
            state.config.away_team.team_id: 0,
        }
        for innings in state.innings:
            totals[innings.batting_team_id] = totals.get(innings.batting_team_id, 0) + innings.runs
        return totals

    def _last_innings_with_history(self, state: MatchState) -> Optional[int]:
        for index in range(len(state.innings) - 1, -1, -1):
            if state.innings[index].history:
                return index
        return None

    def _recalculate_innings(self, innings: InningsState) -> None:
        innings.runs = 0
        innings.wickets = 0
        innings.balls_bowled = 0
        innings.completed = False
        for index, event in enumerate(innings.history, start=1):
            innings.balls_bowled = index
            innings.runs += event.runs_scored
            innings.wickets += 1 if event.is_wicket else 0
