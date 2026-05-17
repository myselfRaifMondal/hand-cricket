"""Tests for DB-backed match persistence through ScoringService."""

from __future__ import annotations

from pathlib import Path

import pytest

from database.db import initialize_database
from database.models import Ball, Innings, Match, Team
from services.match_engine import MatchConfig, MatchEngine, TeamConfig
from services.scoring_service import ScoringService
from utils.constants import InningsStatus, MatchStatus
from utils.helpers import AppSettings, load_settings


def _settings(tmp_path: Path) -> AppSettings:
    base = load_settings()
    return AppSettings(
        application_name=base.application_name,
        database_path=tmp_path / "test.sqlite3",
        log_path=tmp_path / "app.log",
        analytics_cache_path=tmp_path / "cache",
        theme_path=base.theme_path,
        sqlalchemy_echo=False,
        default_overs=base.default_overs,
        default_innings=base.default_innings,
        enable_super_over=base.enable_super_over,
    )


class TestMatchRepositoryCreatesRecords:
    def test_create_match_persists_team_and_match_rows(self, tmp_path: Path) -> None:
        settings = _settings(tmp_path)
        initialize_database(settings)

        from database.db import session_scope
        from database.match_repository import MatchRepository

        repo = MatchRepository(settings)
        match_id, home_id, away_id = repo.create_match(
            home_name="Falcons",
            away_name="Titans",
            batting_first_name="Falcons",
            bowling_first_name="Titans",
            overs=5,
            innings_count=2,
        )

        with session_scope(settings) as session:
            match = session.get(Match, match_id)
            assert match is not None
            assert match.total_overs == 5
            assert match.home_team_id == home_id
            assert match.away_team_id == away_id
            assert match.status == MatchStatus.DRAFT

            home_team = session.get(Team, home_id)
            away_team = session.get(Team, away_id)
            assert home_team is not None and home_team.name == "Falcons"
            assert away_team is not None and away_team.name == "Titans"

    def test_find_or_create_team_is_idempotent(self, tmp_path: Path) -> None:
        settings = _settings(tmp_path)
        initialize_database(settings)

        from database.match_repository import MatchRepository

        repo = MatchRepository(settings)
        id1 = repo.find_or_create_team("Eagles")
        id2 = repo.find_or_create_team("Eagles")
        assert id1 == id2


class TestScoringServicePersistence:
    def _make_service(self, tmp_path: Path) -> ScoringService:
        settings = _settings(tmp_path)
        initialize_database(settings)
        return ScoringService(MatchEngine(), settings=settings)

    def _default_config(self) -> MatchConfig:
        return MatchConfig(
            home_team=TeamConfig(team_id=1, name="Falcons"),
            away_team=TeamConfig(team_id=2, name="Titans"),
            batting_first_team_id=1,
            bowling_first_team_id=2,
            overs=3,
            innings_count=2,
            max_wickets=3,
        )

    def test_record_ball_persists_ball_row(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        svc.create_match(self._default_config())
        svc.start_match()
        svc.record_ball(batting_input=4, bowling_input=2)

        from database.db import session_scope
        settings = _settings(tmp_path)
        with session_scope(settings) as session:
            balls = session.query(Ball).all()
        assert len(balls) == 1
        assert balls[0].batting_input == 4
        assert balls[0].bowling_input == 2
        assert balls[0].runs_scored == 4
        assert balls[0].is_wicket is False

    def test_wicket_ball_is_persisted_correctly(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        svc.create_match(self._default_config())
        svc.start_match()
        svc.record_ball(batting_input=3, bowling_input=3)  # wicket

        from database.db import session_scope
        settings = _settings(tmp_path)
        with session_scope(settings) as session:
            balls = session.query(Ball).all()
        assert len(balls) == 1
        assert balls[0].is_wicket is True
        assert balls[0].runs_scored == 0

    def test_undo_removes_ball_from_db(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        svc.create_match(self._default_config())
        svc.start_match()
        svc.record_ball(batting_input=5, bowling_input=2)
        svc.record_ball(batting_input=6, bowling_input=1)
        svc.undo_last_ball()

        from database.db import session_scope
        settings = _settings(tmp_path)
        with session_scope(settings) as session:
            balls = session.query(Ball).order_by(Ball.sequence_number).all()
        assert len(balls) == 1
        assert balls[0].batting_input == 5

    def test_completed_innings_row_is_updated(self, tmp_path: Path) -> None:
        """After all wickets fall the innings DB row should show COMPLETED."""

        svc = self._make_service(tmp_path)
        svc.create_match(self._default_config())  # max_wickets=3
        svc.start_match()
        # Three matching balls → three wickets → innings complete
        for n in range(1, 4):
            svc.record_ball(batting_input=n, bowling_input=n)

        from database.db import session_scope
        settings = _settings(tmp_path)
        with session_scope(settings) as session:
            innings_rows = session.query(Innings).all()
        # First innings should be completed
        first = next(i for i in innings_rows if i.innings_number == 1)
        assert first.status == InningsStatus.COMPLETED
        assert first.wickets == 3

    def test_full_match_completion_updates_match_status(self, tmp_path: Path) -> None:
        """Playing through both innings should mark the match COMPLETED in DB."""

        svc = self._make_service(tmp_path)
        config = MatchConfig(
            home_team=TeamConfig(team_id=1, name="Alpha"),
            away_team=TeamConfig(team_id=2, name="Beta"),
            batting_first_team_id=1,
            bowling_first_team_id=2,
            overs=1,
            innings_count=2,
            max_wickets=1,
            allow_super_over=False,
        )
        svc.create_match(config)
        svc.start_match()
        # Innings 1: one wicket to end it
        svc.record_ball(batting_input=2, bowling_input=2)
        # Innings 2: one wicket to end it
        svc.record_ball(batting_input=3, bowling_input=3)

        from database.db import session_scope
        settings = _settings(tmp_path)
        with session_scope(settings) as session:
            match = session.query(Match).first()
        assert match is not None
        assert match.status == MatchStatus.COMPLETED
