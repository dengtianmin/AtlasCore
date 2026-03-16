from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    sqlite_path = Path(settings.SQLITE_PATH).expanduser()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_path.touch(exist_ok=True)

    return create_engine(
        settings.sqlite_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, expire_on_commit=False)


def reset_db_state() -> None:
    get_session_factory.cache_clear()
    get_engine.cache_clear()


def initialize_database() -> None:
    Base.metadata.create_all(bind=get_engine())


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
