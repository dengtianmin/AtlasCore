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
from app.services.graph_extraction_service import (
    DEFAULT_GRAPH_EXTRACTION_PROMPT,
    GRAPH_EXTRACTION_MAX_CHARS_PER_CHUNK,
    GraphExtractionService,
)


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
            thinking_enabled=True,
            operator="admin",
        )
        assert model["has_api_key"] is True
        assert "api_key" not in model
    finally:
        db.close()


def test_env_defaults_seed_model_and_prompt_settings(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_PROMPT", "env prompt")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_PROVIDER", "openai-compatible")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_NAME", "gpt-4o-mini")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_KEY", "env-secret-key")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME", None)
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_ENABLED", True)
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_THINKING_ENABLED", False)
    db = get_session_factory()()
    try:
        prompt = service.get_prompt_setting(db)
        model = service.get_model_setting(db)

        assert prompt["prompt_text"] == "env prompt"
        assert model["provider"] == "openai-compatible"
        assert model["model_name"] == "gpt-4o-mini"
        assert model["api_base_url"] == "https://api.openai.com/v1"
        assert model["enabled"] is True
        assert model["thinking_enabled"] is False
        assert model["has_api_key"] is True
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
            thinking_enabled=True,
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


def test_long_markdown_is_split_into_multiple_chunks(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    long_markdown = (
        "# Section A\n\n" + ("Alice uses AtlasCore. " * 400) + "\n\n"
        "# Section B\n\n" + ("Bob studies graphs. " * 400)
    )

    chunks = service._split_markdown_into_chunks(long_markdown, max_chars=GRAPH_EXTRACTION_MAX_CHARS_PER_CHUNK)

    assert len(chunks) >= 2
    assert all(len(chunk) <= GRAPH_EXTRACTION_MAX_CHARS_PER_CHUNK for chunk in chunks)


def test_single_document_extraction_merges_chunk_results(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    long_markdown = (
        "# Chunk One\n\n" + ("Alice uses AtlasCore. " * 400) + "\n\n"
        "# Chunk Two\n\n" + ("Bob uses AtlasCore. " * 400)
    )
    calls: list[str] = []

    async def fake_call_model(*, prompt_text, markdown, model_setting):
        calls.append(markdown)
        person_name = "Alice" if "Alice" in markdown else "Bob"
        return f"""
        {{
          "nodes": [
            {{"name": "{person_name}", "node_type": "person", "description": "{person_name} desc", "tags": ["team"]}},
            {{"name": "AtlasCore", "node_type": "system", "description": "Platform", "tags": ["product"]}}
          ],
          "edges": [
            {{"source": "{person_name}", "target": "AtlasCore", "relation_type": "USES", "relation_label": "uses", "source_type": "person", "target_type": "system"}}
          ]
        }}
        """

    monkeypatch.setattr(service, "_call_model", fake_call_model)

    payload = asyncio.run(
        service._extract_single_document(
            markdown=long_markdown,
            document=type("Doc", (), {"id": uuid4()})(),
            prompt_text=DEFAULT_GRAPH_EXTRACTION_PROMPT,
            model_setting=type("Model", (), {"model_name": "gpt-test"})(),
        )
    )

    assert len(calls) >= 2
    assert len(payload.nodes) == len(calls) * 2
    assert len(payload.edges) == len(calls)


def test_call_model_disables_thinking_when_configured(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "{\"nodes\": [], \"edges\": []}"}}]}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    def fake_async_client(*, timeout, trust_env):
        captured["timeout"] = timeout
        captured["trust_env"] = trust_env
        return FakeClient()

    monkeypatch.setattr("app.services.graph_extraction_service.httpx.AsyncClient", fake_async_client)

    model_setting = type(
        "ModelSetting",
        (),
        {
            "id": uuid4(),
            "provider": "openai-compatible",
            "model_name": "GLM-5",
            "api_base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key_ciphertext": service.secret_box.encrypt("demo-key"),
            "enabled": True,
            "thinking_enabled": False,
            "is_active": True,
            "updated_by": "admin",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        },
    )()

    content = asyncio.run(
        service._call_model(
            prompt_text="prompt",
            markdown="markdown",
            model_setting=model_setting,
        )
    )

    assert content == "{\"nodes\": [], \"edges\": []}"
    assert captured["url"] == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    assert captured["trust_env"] is False
    assert captured["json"]["model"] == "GLM-5"
    assert captured["json"]["thinking"] == {"type": "disabled"}


def test_active_db_model_without_key_falls_back_to_env_key(monkeypatch, tmp_path):
    service = _bootstrap(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_KEY", "env-fallback-key")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME", None)

    db = get_session_factory()()
    try:
        service.update_model_setting(
            db,
            provider="openai-compatible",
            model_name="GLM-5",
            api_base_url="https://open.bigmodel.cn/api/paas/v4",
            api_key="initial-key",
            enabled=True,
            thinking_enabled=False,
            operator="admin",
        )
        active = service.model_repo.get_active(db)
        assert active is not None
        active.api_key_ciphertext = None
        db.add(active)
        db.commit()
        db.refresh(active)

        resolved = service._require_active_model(db)

        assert resolved.api_base_url == "https://open.bigmodel.cn/api/paas/v4"
        assert service.secret_box.decrypt(resolved.api_key_ciphertext) == "env-fallback-key"
        assert resolved.thinking_enabled is False
    finally:
        db.close()
