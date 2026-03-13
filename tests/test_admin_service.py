from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile

from app.admin.document_status import DocumentStatus
from app.integrations.dify.schemas import DifyJobResponse
from app.services.admin_service import AdminDocumentService


class DummyDB:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def _doc(status: str) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        title="doc.txt",
        status=status,
        source_type="upload",
        source_uri="/tmp/doc.txt",
        file_name="doc.txt",
        content_type="text/plain",
        file_size=3,
        created_by=uuid4(),
        created_at=now,
        updated_at=now,
    )


def test_upload_document_creates_metadata(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    admin_id = uuid4()

    upload = UploadFile(filename="doc.txt", file=BytesIO(b"abc"), headers={"content-type": "text/plain"})

    monkeypatch.setattr(service.storage, "save", lambda _: ("/tmp/doc.txt", 3))
    created_doc = _doc(DocumentStatus.UPLOADED.value)

    captured = {}

    def fake_create(*args, **kwargs):
        captured.update(kwargs)
        return created_doc

    monkeypatch.setattr(service.document_repo, "create", fake_create)

    payload = service.upload_document(db, upload=upload, admin_user_id=admin_id)

    assert db.commits == 1
    assert payload["status"] == DocumentStatus.UPLOADED.value
    assert captured["source_type"] == "upload"
    assert captured["created_by"] == admin_id


def test_get_document_not_found():
    service = AdminDocumentService()
    db = DummyDB()
    service.document_repo.get_by_id = lambda *_: None

    with pytest.raises(HTTPException) as exc:
        service.get_document(db, doc_id=uuid4())

    assert exc.value.status_code == 404


def test_delete_document_success(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    doc = _doc(DocumentStatus.UPLOADED.value)

    monkeypatch.setattr(service.document_repo, "get_by_id", lambda *_: doc)
    deleted = {"ok": False}

    def fake_delete(*args, **kwargs):
        deleted["ok"] = True

    monkeypatch.setattr(service.document_repo, "delete", fake_delete)

    service.delete_document(db, doc_id=doc.id)

    assert deleted["ok"] is True
    assert db.commits == 1


def test_trigger_graph_sync_updates_status_and_creates_record(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    doc = _doc(DocumentStatus.UPLOADED.value)
    updated = _doc(DocumentStatus.GRAPH_PENDING.value)

    monkeypatch.setattr(service.document_repo, "get_by_id", lambda *_: doc)
    monkeypatch.setattr(service.document_repo, "update_status", lambda *args, **kwargs: updated)

    record_id = uuid4()
    monkeypatch.setattr(
        service.sync_repo,
        "create",
        lambda *args, **kwargs: SimpleNamespace(id=record_id),
    )

    payload = service.trigger_graph_sync(db, doc_id=doc.id)

    assert payload["target_system"] == "graph"
    assert payload["status"] == DocumentStatus.GRAPH_PENDING.value
    assert payload["sync_record_id"] == record_id
    assert db.commits == 1


def test_trigger_dify_index_updates_status_and_creates_record(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    doc = _doc(DocumentStatus.UPLOADED.value)
    updated = _doc(DocumentStatus.INDEXED.value)

    monkeypatch.setattr(service.document_repo, "get_by_id", lambda *_: doc)
    monkeypatch.setattr(service.document_repo, "update_status", lambda *args, **kwargs: updated)
    monkeypatch.setattr(
        service.dify_client,
        "enqueue_document_index",
        lambda *_args, **_kwargs: DifyJobResponse(
            job_id="dify-job-1",
            status="queued",
            message="queued from test",
        ),
    )

    record_id = uuid4()
    monkeypatch.setattr(
        service.sync_repo,
        "create",
        lambda *args, **kwargs: SimpleNamespace(id=record_id),
    )

    payload = service.trigger_dify_index(db, doc_id=doc.id)

    assert payload["target_system"] == "dify"
    assert payload["status"] == DocumentStatus.INDEXED.value
    assert payload["sync_record_id"] == record_id
    assert payload["message"] == "queued from test"
    assert db.commits == 1
