from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set DATABASE_URL before using PostgreSQL features."
        )

    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
