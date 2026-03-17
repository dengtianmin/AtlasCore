import asyncio
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.db.session import get_session_factory, initialize_database, reset_db_state
from app.graph.db import initialize_graph_database, reset_graph_db_state
from app.repositories.document_repo import DocumentRepository
from app.services.graph_extraction_service import DEFAULT_GRAPH_EXTRACTION_PROMPT, GraphExtractionService


def _bootstrap(monkeypatch, tmp_path) -> GraphExtractionService:
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime.db"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph.db"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "imports"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "JWT_SECRET", "graph-secret")
    reset_db_state()
    reset_graph_db_state()
    initialize_database()
    initialize_graph_database()
    return GraphExtractionService()


def test_upload_and_list_files(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    db = get_session_factory()()
    try:
        md_file = UploadFile(filename="knowledge.md", file=BytesIO(b"# AtlasCore"), headers={"content-type": "text/markdown"})
        sqlite_file = UploadFile(filename="graph.db", file=BytesIO(b"sqlite"), headers={"content-type": "application/octet-stream"})

        md_payload = service.upload_file(db, upload=md_file, admin_user_id=uuid4(), file_type="md")
        sqlite_payload = service.upload_file(db, upload=sqlite_file, admin_user_id=uuid4(), file_type="sqlite")
        md_list = service.list_files(db, file_type="md", limit=20, offset=0)
        sqlite_list = service.list_files(db, file_type="sqlite", limit=20, offset=0)

        assert md_payload["status"] == "pending_extraction"
        assert sqlite_payload["status"] == "registered"
        assert md_list["items"][0]["file_type"] == "md"
        assert sqlite_list["items"][0]["file_type"] == "sqlite"
    finally:
        db.close()


def test_prompt_and_model_settings_mask_api_key(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    db = get_session_factory()()
    try:
        prompt = service.get_prompt_setting(db)
        assert prompt["prompt_text"] == DEFAULT_GRAPH_EXTRACTION_PROMPT

        model = service.update_model_setting(
            db,
            provider="openai-compatible",
            model_name="gpt-test",
            api_base_url="https://llm.example.com/v1",
            api_key="secret-key",
            enabled=True,
            operator="admin",
        )
        assert model["has_api_key"] is True
        assert "api_key" not in model
    finally:
        db.close()


def test_create_extraction_task_builds_graph(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    db = get_session_factory()()
    repo = DocumentRepository()
    try:
        service.update_model_setting(
            db,
            provider="openai-compatible",
            model_name="gpt-test",
            api_base_url="https://llm.example.com/v1",
            api_key="secret-key",
            enabled=True,
            operator="admin",
        )

        now = datetime.now(UTC)
        first_path = Path(settings.DOCUMENT_LOCAL_STORAGE_DIR) / "doc1.md"
        second_path = Path(settings.DOCUMENT_LOCAL_STORAGE_DIR) / "doc2.md"
        first_path.parent.mkdir(parents=True, exist_ok=True)
        first_path.write_text("# Alice", encoding="utf-8")
        second_path.write_text("# Bob", encoding="utf-8")
        first = repo.create(
            db,
            filename="doc1.md",
            file_type="md",
            source_type="upload",
            status="pending_extraction",
            uploaded_at=now,
            created_by=None,
            local_path=str(first_path),
            source_uri=str(first_path),
            mime_type="text/markdown",
            content_type="text/markdown",
            file_size=10,
            file_extension="md",
            created_at=now,
        )
        second = repo.create(
            db,
            filename="doc2.md",
            file_type="md",
            source_type="upload",
            status="pending_extraction",
            uploaded_at=now,
            created_by=None,
            local_path=str(second_path),
            source_uri=str(second_path),
            mime_type="text/markdown",
            content_type="text/markdown",
            file_size=10,
            file_extension="md",
            created_at=now,
        )
        db.commit()

        async def fake_call_model(*, prompt_text, markdown, model_setting):
            assert prompt_text
            assert markdown.startswith("#")
            assert model_setting.model_name == "gpt-test"
            return """
            {
              "nodes": [
                {"name": "Alice", "node_type": "person", "description": "Researcher", "tags": ["team-a"]},
                {"name": "AtlasCore", "node_type": "system", "description": "Platform", "tags": ["product"]}
              ],
              "edges": [
                {"source": "Alice", "target": "AtlasCore", "relation_type": "USES", "relation_label": "uses", "source_type": "person", "target_type": "system"}
              ]
            }
            """

        monkeypatch.setattr(service, "_call_model", fake_call_model)

        payload = asyncio.run(
            service.create_extraction_task(
                db,
                document_ids=[UUID(str(first.id)), UUID(str(second.id))],
                operator="admin",
            )
        )

        assert payload["status"] == "succeeded"
        assert payload["output_graph_version"].startswith("extract_")

        refreshed_first = repo.get_by_id(db, first.id)
        refreshed_second = repo.get_by_id(db, second.id)
        assert refreshed_first is not None and refreshed_first.status == "applied_to_graph"
        assert refreshed_second is not None and refreshed_second.status == "applied_to_graph"
    finally:
        db.close()
