"""Unit tests for the hand cricket match engine."""

from __future__ import annotations

from services.match_engine import MatchConfig, MatchEngine, TeamConfig
from utils.constants import MatchStatus


def build_config(allow_super_over: bool = False) -> MatchConfig:
    return MatchConfig(
        home_team=TeamConfig(team_id=1, name="Falcons"),
        away_team=TeamConfig(team_id=2, name="Titans"),
        batting_first_team_id=1,
        bowling_first_team_id=2,
        overs=1,
        innings_count=2,
        max_wickets=2,
        allow_super_over=allow_super_over,
    )


def test_matching_inputs_produce_wicket() -> None:
    engine = MatchEngine()
    state = engine.create_match(build_config())
    engine.start_match(state)

    event = engine.record_ball(state, 3, 3)

    assert event.is_wicket is True
    assert state.current_innings().wickets == 1
    assert state.current_innings().runs == 0


def test_second_innings_chase_completes_match() -> None:
    engine = MatchEngine()
    state = engine.create_match(build_config())
    engine.start_match(state)

    engine.record_ball(state, 6, 1)
    engine.record_ball(state, 4, 2)
    engine.record_ball(state, 1, 1)
    engine.record_ball(state, 2, 2)

    assert state.current_innings_index == 1
    assert state.current_innings().target == 11

    engine.record_ball(state, 6, 1)
    engine.record_ball(state, 5, 4)

    assert state.status == MatchStatus.COMPLETED
    assert state.winner_team_id == 2
    assert "won by" in state.result_text


def test_undo_last_ball_rewinds_score() -> None:
    engine = MatchEngine()
    state = engine.create_match(build_config())
    engine.start_match(state)
    engine.record_ball(state, 2, 1)
    engine.record_ball(state, 4, 2)

    removed = engine.undo_last_ball(state)

    assert removed.runs_scored == 4
    assert state.current_innings().runs == 2
    assert state.current_innings().balls_bowled == 1


def test_tie_triggers_super_over_when_enabled() -> None:
    engine = MatchEngine()
    state = engine.create_match(build_config(allow_super_over=True))
    engine.start_match(state)

    engine.record_ball(state, 4, 1)
    engine.record_ball(state, 2, 2)
    engine.record_ball(state, 3, 3)
    engine.record_ball(state, 4, 1)
    engine.record_ball(state, 2, 2)
    engine.record_ball(state, 3, 3)

    assert len(state.innings) == 4
    assert state.current_innings().is_super_over is True
    assert state.status == MatchStatus.LIVE


def test_complete_current_innings_advances_to_next_innings() -> None:
    engine = MatchEngine()
    state = engine.create_match(build_config())
    engine.start_match(state)
    engine.record_ball(state, 4, 1)

    engine.complete_current_innings(state)

    assert state.current_innings_index == 1
    assert state.current_innings().target == 5
    assert state.status == MatchStatus.LIVE


def test_complete_current_innings_requires_live_match() -> None:
    engine = MatchEngine()
    state = engine.create_match(build_config())

    try:
        engine.complete_current_innings(state)
    except ValueError as error:
        assert "Only a live match innings can be completed." in str(error)
    else:
        raise AssertionError("Expected ValueError for non-live innings completion")
