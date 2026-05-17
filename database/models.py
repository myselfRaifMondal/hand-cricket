"""SQLAlchemy ORM models for the Hand Cricket application."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from utils.constants import InningsStatus, MatchStatus, PlayerRole, TossDecision


class Base(DeclarativeBase):
    """Declarative SQLAlchemy base."""


class TimestampMixin:
    """Reusable created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Tournament(TimestampMixin, Base):
    """Tournament metadata and grouping."""

    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    location: Mapped[Optional[str]] = mapped_column(String(120))
    start_date: Mapped[Optional[date]] = mapped_column(Date())
    end_date: Mapped[Optional[date]] = mapped_column(Date())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    matches: Mapped[list["Match"]] = relationship(back_populates="tournament")


class Team(TimestampMixin, Base):
    """Hand cricket team."""

    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("name", name="uq_team_name"),
        Index("ix_teams_name", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_name: Mapped[str] = mapped_column(String(12), nullable=False)
    logo_path: Mapped[Optional[str]] = mapped_column(String(255))
    captain_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))

    players: Mapped[list["Player"]] = relationship(
        back_populates="team",
        foreign_keys="Player.team_id",
        cascade="all, delete-orphan",
    )
    captain: Mapped[Optional["Player"]] = relationship(
        foreign_keys=[captain_player_id],
        post_update=True,
    )
    home_matches: Mapped[list["Match"]] = relationship(
        back_populates="home_team",
        foreign_keys="Match.home_team_id",
    )
    away_matches: Mapped[list["Match"]] = relationship(
        back_populates="away_team",
        foreign_keys="Match.away_team_id",
    )


class Player(TimestampMixin, Base):
    """Player roster and aggregate statistics."""

    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("team_id", "jersey_number", name="uq_player_jersey_per_team"),
        Index("ix_players_name", "name"),
        Index("ix_players_team", "team_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    jersey_number: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[PlayerRole] = mapped_column(Enum(PlayerRole), nullable=False, default=PlayerRole.ALL_ROUNDER)
    batting_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    balls_faced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wickets_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    balls_bowled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_matches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    highest_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    strike_rate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    economy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    team: Mapped[Team] = relationship(back_populates="players", foreign_keys=[team_id])
    ball_events_as_batter: Mapped[list["Ball"]] = relationship(foreign_keys="Ball.batter_id", back_populates="batter")
    ball_events_as_bowler: Mapped[list["Ball"]] = relationship(foreign_keys="Ball.bowler_id", back_populates="bowler")
    statistics: Mapped[list["Statistic"]] = relationship(back_populates="player", cascade="all, delete-orphan")


class Match(TimestampMixin, Base):
    """Match metadata and match-level result state."""

    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_status_scheduled", "status", "scheduled_at"),
        Index("ix_matches_tournament", "tournament_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tournament_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournaments.id", ondelete="SET NULL"))
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    toss_winner_team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    batting_first_team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    bowling_first_team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    winner_team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    venue: Mapped[Optional[str]] = mapped_column(String(120))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime())
    total_overs: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    innings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    current_innings_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), nullable=False, default=MatchStatus.DRAFT)
    toss_decision: Mapped[Optional[TossDecision]] = mapped_column(Enum(TossDecision))
    is_super_over: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    result_summary: Mapped[Optional[str]] = mapped_column(Text())

    tournament: Mapped[Optional[Tournament]] = relationship(back_populates="matches")
    home_team: Mapped[Team] = relationship(back_populates="home_matches", foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(back_populates="away_matches", foreign_keys=[away_team_id])
    innings: Mapped[list["Innings"]] = relationship(back_populates="match", cascade="all, delete-orphan", order_by="Innings.innings_number")
    statistics: Mapped[list["Statistic"]] = relationship(back_populates="match", cascade="all, delete-orphan")


class Innings(TimestampMixin, Base):
    """A single innings with ball-by-ball event history."""

    __tablename__ = "innings"
    __table_args__ = (
        UniqueConstraint("match_id", "innings_number", name="uq_match_innings_number"),
        Index("ix_innings_match", "match_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    batting_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    bowling_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    innings_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[InningsStatus] = mapped_column(Enum(InningsStatus), nullable=False, default=InningsStatus.PENDING)
    is_super_over: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    target_runs: Mapped[Optional[int]] = mapped_column(Integer)
    runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balls_bowled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime())

    match: Mapped[Match] = relationship(back_populates="innings")
    batting_team: Mapped[Team] = relationship(foreign_keys=[batting_team_id])
    bowling_team: Mapped[Team] = relationship(foreign_keys=[bowling_team_id])
    balls: Mapped[list["Ball"]] = relationship(back_populates="innings", cascade="all, delete-orphan", order_by="Ball.sequence_number")


class Ball(TimestampMixin, Base):
    """Immutable ball event used for score reconstruction and analytics."""

    __tablename__ = "balls"
    __table_args__ = (
        UniqueConstraint("innings_id", "sequence_number", name="uq_ball_sequence_per_innings"),
        Index("ix_balls_innings_sequence", "innings_id", "sequence_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    batter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    bowler_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    over_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ball_in_over: Mapped[int] = mapped_column(Integer, nullable=False)
    batting_input: Mapped[int] = mapped_column(Integer, nullable=False)
    bowling_input: Mapped[int] = mapped_column(Integer, nullable=False)
    runs_scored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_wicket: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    commentary: Mapped[Optional[str]] = mapped_column(String(255))

    innings: Mapped[Innings] = relationship(back_populates="balls")
    batter: Mapped[Optional[Player]] = relationship(foreign_keys=[batter_id], back_populates="ball_events_as_batter")
    bowler: Mapped[Optional[Player]] = relationship(foreign_keys=[bowler_id], back_populates="ball_events_as_bowler")


class Statistic(TimestampMixin, Base):
    """Per-match player statistics used by dashboards and exports."""

    __tablename__ = "statistics"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_statistic_match_player"),
        Index("ix_statistics_match_team", "match_id", "team_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    runs_scored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balls_faced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wickets_taken: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balls_bowled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strike_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    economy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    match: Mapped[Match] = relationship(back_populates="statistics")
    player: Mapped[Player] = relationship(back_populates="statistics")
    team: Mapped[Team] = relationship()
