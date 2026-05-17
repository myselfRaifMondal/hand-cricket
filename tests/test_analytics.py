"""Tests for analytics transformations."""

from __future__ import annotations

from services.analytics_service import AnalyticsService


def test_analytics_bundle_contains_expected_shapes() -> None:
    snapshot = {
        "batting_team_name": "Falcons",
        "score": 12,
        "wickets": 2,
        "overs": "1.0",
        "target": 18,
        "balls_remaining": 12,
        "current_run_rate": 12.0,
        "history": [
            {
                "innings_number": 1,
                "sequence_number": 1,
                "batting_input": 4,
                "bowling_input": 1,
                "runs_scored": 4,
                "is_wicket": False,
                "total_score_after": 4,
                "wickets_after": 0,
                "over_notation": "0.1",
            },
            {
                "innings_number": 1,
                "sequence_number": 2,
                "batting_input": 2,
                "bowling_input": 2,
                "runs_scored": 0,
                "is_wicket": True,
                "total_score_after": 4,
                "wickets_after": 1,
                "over_notation": "0.2",
            },
            {
                "innings_number": 1,
                "sequence_number": 3,
                "batting_input": 6,
                "bowling_input": 3,
                "runs_scored": 6,
                "is_wicket": False,
                "total_score_after": 10,
                "wickets_after": 1,
                "over_notation": "0.3",
            },
        ],
    }

    bundle = AnalyticsService().build_bundle(snapshot)

    assert len(bundle.ball_frame.index) == 3
    assert bundle.over_summary.iloc[0]["runs"] == 10
    assert bundle.over_summary.iloc[0]["wickets"] == 1
    assert bundle.innings_summary.iloc[0]["batting_team"] == "Falcons"
    assert 0.0 <= bundle.win_probability <= 100.0