from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class GraphBase(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)


@lru_cache(maxsize=1)
def get_graph_engine() -> Engine:
    sqlite_path = settings.graph_instance_path
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_path.touch(exist_ok=True)
    return create_engine(
        settings.graph_sqlite_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )


@lru_cache(maxsize=1)
def get_graph_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_graph_engine(), autocommit=False, autoflush=False, expire_on_commit=False)


def get_graph_session() -> Generator[Session, None, None]:
    session = get_graph_session_factory()()
    try:
        yield session
    finally:
        session.close()


def reset_graph_db_state() -> None:
    get_graph_session_factory.cache_clear()
    get_graph_engine.cache_clear()


def initialize_graph_database() -> None:
    import app.models.graph_edge  # noqa: F401
    import app.models.graph_node  # noqa: F401
    import app.models.graph_sync_record  # noqa: F401
    import app.models.graph_version  # noqa: F401

    GraphBase.metadata.create_all(bind=get_graph_engine())
