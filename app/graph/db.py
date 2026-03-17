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
    import app.models.graph_node_source  # noqa: F401
    import app.models.graph_sync_record  # noqa: F401
    import app.models.graph_version  # noqa: F401

    engine = get_graph_engine()
    GraphBase.metadata.create_all(bind=engine)
    _ensure_graph_sqlite_schema_alignment(engine)


def _sqlite_table_columns(connection, table_name: str) -> set[str]:
    rows = connection.exec_driver_sql(f"PRAGMA table_info('{table_name}')").fetchall()
    return {str(row[1]) for row in rows}


def _ensure_graph_sqlite_schema_alignment(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    additive_columns: dict[str, list[str]] = {
        "graph_nodes": [
            "ALTER TABLE graph_nodes ADD COLUMN normalized_name VARCHAR(255)",
        ],
        "graph_edges": [
            "ALTER TABLE graph_edges ADD COLUMN source_document_id VARCHAR(36)",
        ],
        "graph_versions": [
            "ALTER TABLE graph_versions ADD COLUMN version_type VARCHAR(32)",
            "ALTER TABLE graph_versions ADD COLUMN source_document_ids TEXT",
            "ALTER TABLE graph_versions ADD COLUMN operator VARCHAR(100)",
        ],
    }

    with engine.begin() as connection:
        for table_name, statements in additive_columns.items():
            existing_columns = _sqlite_table_columns(connection, table_name)
            if not existing_columns:
                continue

            for statement in statements:
                column_name = statement.split(" ADD COLUMN ", 1)[1].split(" ", 1)[0]
                if column_name not in existing_columns:
                    connection.exec_driver_sql(statement)
                    existing_columns.add(column_name)

        node_columns = _sqlite_table_columns(connection, "graph_nodes")
        if "normalized_name" in node_columns:
            connection.exec_driver_sql(
                """
                UPDATE graph_nodes
                SET normalized_name = LOWER(REPLACE(TRIM(COALESCE(name, id)), ' ', ''))
                WHERE normalized_name IS NULL OR normalized_name = ''
                """
            )
