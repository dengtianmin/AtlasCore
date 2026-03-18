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


def _sqlite_table_columns(connection, table_name: str) -> set[str]:
    rows = connection.exec_driver_sql(f"PRAGMA table_info('{table_name}')").fetchall()
    return {str(row[1]) for row in rows}


def _ensure_sqlite_schema_alignment(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    additive_columns: dict[str, list[str]] = {
        "qa_logs": [
            "ALTER TABLE qa_logs ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'succeeded'",
            "ALTER TABLE qa_logs ADD COLUMN provider_message_id VARCHAR(128)",
            "ALTER TABLE qa_logs ADD COLUMN error_code VARCHAR(64)",
            "ALTER TABLE qa_logs ADD COLUMN user_id VARCHAR(36)",
            "ALTER TABLE qa_logs ADD COLUMN student_id_snapshot VARCHAR(10)",
            "ALTER TABLE qa_logs ADD COLUMN name_snapshot VARCHAR(50)",
        ],
        "users": [
            "ALTER TABLE users ADD COLUMN last_login_at DATETIME",
        ],
        "documents": [
            "ALTER TABLE documents ADD COLUMN file_type VARCHAR(32) NOT NULL DEFAULT 'generic'",
            "ALTER TABLE documents ADD COLUMN created_at DATETIME",
            "ALTER TABLE documents ADD COLUMN last_sync_target VARCHAR(32)",
            "ALTER TABLE documents ADD COLUMN last_sync_status VARCHAR(32)",
            "ALTER TABLE documents ADD COLUMN last_sync_at DATETIME",
            "ALTER TABLE documents ADD COLUMN local_path TEXT",
            "ALTER TABLE documents ADD COLUMN mime_type VARCHAR(120)",
            "ALTER TABLE documents ADD COLUMN file_extension VARCHAR(32)",
            "ALTER TABLE documents ADD COLUMN dify_upload_file_id VARCHAR(128)",
            "ALTER TABLE documents ADD COLUMN dify_uploaded_at DATETIME",
            "ALTER TABLE documents ADD COLUMN dify_sync_status VARCHAR(32)",
            "ALTER TABLE documents ADD COLUMN dify_error_code VARCHAR(64)",
            "ALTER TABLE documents ADD COLUMN dify_error_message TEXT",
            "ALTER TABLE documents ADD COLUMN extraction_task_id VARCHAR(36)",
            "ALTER TABLE documents ADD COLUMN graph_extraction_chunk_count INTEGER",
            "ALTER TABLE documents ADD COLUMN graph_extraction_completed_chunks INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE documents ADD COLUMN graph_extraction_payloads_json TEXT",
            "ALTER TABLE documents ADD COLUMN graph_extraction_last_error TEXT",
            "ALTER TABLE documents ADD COLUMN removed_from_graph_at DATETIME",
            "ALTER TABLE documents ADD COLUMN invalidated_at DATETIME",
            "ALTER TABLE documents ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1",
        ],
        "graph_model_settings": [
            "ALTER TABLE graph_model_settings ADD COLUMN thinking_enabled BOOLEAN NOT NULL DEFAULT 1",
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

        document_columns = _sqlite_table_columns(connection, "documents")
        if "file_type" in document_columns:
            connection.exec_driver_sql(
                """
                UPDATE documents
                SET file_type = CASE
                    WHEN LOWER(COALESCE(file_extension, '')) IN ('md', 'markdown') THEN 'md'
                    WHEN LOWER(COALESCE(file_extension, '')) IN ('db', 'sqlite', 'sqlite3') THEN 'sqlite'
                    ELSE COALESCE(file_type, 'generic')
                END
                WHERE file_type IS NULL OR file_type = '' OR file_type = 'generic'
                """
            )
        if "created_at" in document_columns:
            connection.exec_driver_sql(
                """
                UPDATE documents
                SET created_at = COALESCE(created_at, uploaded_at, CURRENT_TIMESTAMP)
                WHERE created_at IS NULL
                """
            )
        if "graph_extraction_completed_chunks" in document_columns:
            connection.exec_driver_sql(
                """
                UPDATE documents
                SET graph_extraction_completed_chunks = COALESCE(graph_extraction_completed_chunks, 0)
                WHERE graph_extraction_completed_chunks IS NULL
                """
            )


def initialize_database() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_schema_alignment(engine)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
