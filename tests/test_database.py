"""Integration tests for ORM relationships and database bootstrapping."""

from __future__ import annotations

from pathlib import Path

from database.db import initialize_database, session_scope
from database.models import Ball, Innings, Match, Player, Team
from utils.constants import MatchStatus, PlayerRole
from utils.helpers import AppSettings


def build_settings(database_path: Path) -> AppSettings:
    return AppSettings(
        database_path=database_path,
        log_path=database_path.parent / "test.log",
        analytics_cache_path=database_path.parent / "cache",
        theme_path=Path("ui/themes/dark.qss"),
    )


def test_database_initialization_and_relationships(tmp_path: Path) -> None:
    settings = build_settings(tmp_path / "app.sqlite3")
    initialize_database(settings)

    with session_scope(settings) as session:
        falcons = Team(name="Falcons", short_name="FAL")
        titans = Team(name="Titans", short_name="TTN")
        session.add_all([falcons, titans])
        session.flush()

        captain = Player(team_id=falcons.id, name="A. Ray", jersey_number=7, role=PlayerRole.ALL_ROUNDER)
        bowler = Player(team_id=titans.id, name="R. Das", jersey_number=11, role=PlayerRole.BOWLER)
        session.add_all([captain, bowler])
        session.flush()

        falcons.captain_player_id = captain.id
        match = Match(
            home_team_id=falcons.id,
            away_team_id=titans.id,
            total_overs=5,
            innings_count=2,
            status=MatchStatus.LIVE,
            batting_first_team_id=falcons.id,
            bowling_first_team_id=titans.id,
        )
        session.add(match)
        session.flush()

        innings = Innings(
            match_id=match.id,
            batting_team_id=falcons.id,
            bowling_team_id=titans.id,
            innings_number=1,
            runs=4,
            wickets=0,
            balls_bowled=1,
        )
        session.add(innings)
        session.flush()

        ball = Ball(
            innings_id=innings.id,
            batter_id=captain.id,
            bowler_id=bowler.id,
            sequence_number=1,
            over_number=0,
            ball_in_over=1,
            batting_input=4,
            bowling_input=1,
            runs_scored=4,
            is_wicket=False,
        )
        session.add(ball)

    with session_scope(settings) as session:
        stored_match = session.query(Match).one()
        assert stored_match.home_team.name == "Falcons"
        assert stored_match.innings[0].balls[0].runs_scored == 4
        assert stored_match.innings[0].balls[0].batter.name == "A. Ray"