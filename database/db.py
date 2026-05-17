"""Database bootstrap and session management."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base
from utils.helpers import AppSettings, ensure_runtime_directories

_engine_cache: dict[Path, Engine] = {}
_session_factory_cache: dict[Path, sessionmaker[Session]] = {}


def build_database_url(settings: AppSettings) -> str:
    """Return the SQLite database URL for the current settings."""

    return f"sqlite:///{settings.database_path}"


def get_engine(settings: AppSettings) -> Engine:
    """Return a cached SQLAlchemy engine for the configured database path."""

    if settings.database_path not in _engine_cache:
        ensure_runtime_directories(settings)
        engine = create_engine(
            build_database_url(settings),
            echo=settings.sqlalchemy_echo,
            future=True,
        )

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection: Connection, _connection_record: object) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        _engine_cache[settings.database_path] = engine
    return _engine_cache[settings.database_path]


def get_session_factory(settings: AppSettings) -> sessionmaker[Session]:
    """Return a cached session factory for the configured engine."""

    if settings.database_path not in _session_factory_cache:
        _session_factory_cache[settings.database_path] = sessionmaker(
            bind=get_engine(settings),
            expire_on_commit=False,
            class_=Session,
        )
    return _session_factory_cache[settings.database_path]


def initialize_database(settings: AppSettings) -> None:
    """Create all tables for the application."""

    engine = get_engine(settings)
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope(settings: AppSettings) -> Iterator[Session]:
    """Yield a transactional SQLAlchemy session."""

    session = get_session_factory(settings)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
