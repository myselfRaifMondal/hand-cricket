"""Repository for persisting match lifecycle to SQLite."""

from __future__ import annotations

from typing import Optional

from database.db import session_scope
from database.models import Ball, Innings, Match, Team
from utils.constants import InningsStatus, MatchStatus
from utils.helpers import AppSettings


class MatchRepository:
    """Thin persistence helper for Match, Innings, and Ball records."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    # ------------------------------------------------------------------
    # Team helpers
    # ------------------------------------------------------------------

    def find_or_create_team(self, name: str) -> int:
        """Return the DB id of the team with *name*, creating it if absent."""

        with session_scope(self.settings) as session:
            team = session.query(Team).filter(Team.name == name).first()
            if team is None:
                short_name = name[:4].upper()
                team = Team(name=name, short_name=short_name)
                session.add(team)
                session.flush()
            return team.id

    # ------------------------------------------------------------------
    # Match creation
    # ------------------------------------------------------------------

    def create_match(
        self,
        home_name: str,
        away_name: str,
        batting_first_name: str,
        bowling_first_name: str,
        overs: int,
        innings_count: int,
    ) -> tuple[int, int, int]:
        """Create team + match records and return (match_id, home_id, away_id)."""

        home_id = self.find_or_create_team(home_name)
        away_id = self.find_or_create_team(away_name)
        batting_id = home_id if batting_first_name == home_name else away_id
        bowling_id = away_id if batting_first_name == home_name else home_id

        with session_scope(self.settings) as session:
            match = Match(
                home_team_id=home_id,
                away_team_id=away_id,
                batting_first_team_id=batting_id,
                bowling_first_team_id=bowling_id,
                total_overs=overs,
                innings_count=innings_count,
                status=MatchStatus.DRAFT,
            )
            session.add(match)
            session.flush()
            return match.id, home_id, away_id

    def mark_match_live(self, match_id: int) -> None:
        """Transition the match to LIVE status."""

        with session_scope(self.settings) as session:
            match = session.get(Match, match_id)
            if match is not None:
                match.status = MatchStatus.LIVE

    def complete_match(
        self,
        match_id: int,
        winner_team_id: Optional[int],
        result_summary: str,
    ) -> None:
        """Mark the match COMPLETED and store the winner."""

        with session_scope(self.settings) as session:
            match = session.get(Match, match_id)
            if match is not None:
                match.status = MatchStatus.COMPLETED
                match.winner_team_id = winner_team_id
                match.result_summary = result_summary

    # ------------------------------------------------------------------
    # Innings management
    # ------------------------------------------------------------------

    def ensure_innings(
        self,
        match_id: int,
        innings_number: int,
        batting_team_id: int,
        bowling_team_id: int,
        target_runs: Optional[int] = None,
    ) -> int:
        """Return innings_id, creating the innings record if it doesn't exist yet."""

        with session_scope(self.settings) as session:
            innings = (
                session.query(Innings)
                .filter(Innings.match_id == match_id, Innings.innings_number == innings_number)
                .first()
            )
            if innings is not None:
                return innings.id
            innings = Innings(
                match_id=match_id,
                innings_number=innings_number,
                batting_team_id=batting_team_id,
                bowling_team_id=bowling_team_id,
                status=InningsStatus.LIVE,
                target_runs=target_runs,
            )
            session.add(innings)
            session.flush()
            return innings.id

    def complete_innings(
        self,
        innings_id: int,
        runs: int,
        wickets: int,
        balls_bowled: int,
    ) -> None:
        """Persist final innings totals and mark it COMPLETED."""

        with session_scope(self.settings) as session:
            innings = session.get(Innings, innings_id)
            if innings is not None:
                innings.status = InningsStatus.COMPLETED
                innings.runs = runs
                innings.wickets = wickets
                innings.balls_bowled = balls_bowled

    # ------------------------------------------------------------------
    # Ball persistence
    # ------------------------------------------------------------------

    def append_ball(
        self,
        innings_id: int,
        sequence_number: int,
        over_number: int,
        ball_in_over: int,
        batting_input: int,
        bowling_input: int,
        runs_scored: int,
        is_wicket: bool,
    ) -> None:
        """Insert an immutable ball event row."""

        with session_scope(self.settings) as session:
            ball = Ball(
                innings_id=innings_id,
                sequence_number=sequence_number,
                over_number=over_number,
                ball_in_over=ball_in_over,
                batting_input=batting_input,
                bowling_input=bowling_input,
                runs_scored=runs_scored,
                is_wicket=is_wicket,
            )
            session.add(ball)

    def delete_last_ball(self, innings_id: int) -> None:
        """Delete the most recent ball in *innings_id* (undo support)."""

        with session_scope(self.settings) as session:
            ball = (
                session.query(Ball)
                .filter(Ball.innings_id == innings_id)
                .order_by(Ball.sequence_number.desc())
                .first()
            )
            if ball is not None:
                session.delete(ball)

    def delete_all_balls(self, innings_id: int) -> None:
        """Delete every ball in the innings (innings reset support)."""

        with session_scope(self.settings) as session:
            session.query(Ball).filter(Ball.innings_id == innings_id).delete()
