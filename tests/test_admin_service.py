from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import asyncio
import pytest
from fastapi import HTTPException, UploadFile

from app.admin.document_status import DocumentStatus
from app.admin.storage import StoredDocument
from app.core.config import settings
from app.integrations.dify.exceptions import DifyFileTooLargeError, DifyUnsupportedFileTypeError
from app.integrations.dify.schemas import DifyUploadedFile
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
        filename="doc.txt",
        status=status,
        source_type="upload",
        uploaded_at=now,
        synced_to_dify=False,
        synced_to_graph=False,
        note=None,
        local_path="/tmp/doc.txt",
        source_uri="/tmp/doc.txt",
        mime_type="text/plain",
        content_type="text/plain",
        file_size=3,
        file_extension="txt",
        dify_upload_file_id=None,
        dify_uploaded_at=None,
        dify_sync_status="not_synced",
        dify_error_code=None,
        dify_error_message=None,
        created_by=uuid4(),
        created_at=now,
        last_sync_target=None,
        last_sync_status=None,
        last_sync_at=None,
    )


def test_upload_document_creates_metadata(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    admin_id = uuid4()

    upload = UploadFile(filename="doc.txt", file=BytesIO(b"abc"), headers={"content-type": "text/plain"})

    monkeypatch.setattr(
        service.storage,
        "save",
        lambda _: StoredDocument(
            local_path="/tmp/doc.txt",
            file_size=3,
            mime_type="text/plain",
            file_extension="txt",
            stored_filename="stored-doc.txt",
        ),
    )
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
    assert captured["filename"] == "doc.txt"
    assert captured["local_path"] == "/tmp/doc.txt"
    assert captured["mime_type"] == "text/plain"
    assert captured["file_extension"] == "txt"
    assert captured["dify_sync_status"] == "not_synced"
    assert "created_at" in captured


def test_upload_document_rejects_empty_file():
    service = AdminDocumentService()
    db = DummyDB()

    upload = UploadFile(filename="empty.txt", file=BytesIO(b""), headers={"content-type": "text/plain"})

    with pytest.raises(HTTPException) as exc:
        service.upload_document(db, upload=upload, admin_user_id=uuid4())

    assert exc.value.status_code == 400
    assert exc.value.detail == "Uploaded file is empty"


def test_upload_document_rejects_disallowed_extension(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    monkeypatch.setattr(settings, "DOCUMENT_ALLOWED_EXTENSIONS", "pdf")

    upload = UploadFile(filename="doc.txt", file=BytesIO(b"abc"), headers={"content-type": "text/plain"})

    with pytest.raises(HTTPException) as exc:
        service.upload_document(db, upload=upload, admin_user_id=uuid4())

    assert exc.value.status_code == 400
    assert exc.value.detail == "Uploaded file type is not allowed"


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
    monkeypatch.setattr(service.storage, "delete", lambda *_: None)
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

    monkeypatch.setattr(service.document_repo, "mark_synced", lambda *args, **kwargs: updated)

    payload = service.trigger_graph_sync(db, doc_id=doc.id)

    assert payload["target_system"] == "graph"
    assert payload["status"] == DocumentStatus.GRAPH_PENDING.value
    assert db.commits == 1


def test_trigger_dify_index_updates_status_and_creates_record(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    doc = _doc(DocumentStatus.UPLOADED.value)
    updated = _doc(DocumentStatus.SYNCED.value)
    updated.synced_to_dify = True
    updated.dify_upload_file_id = "dify-file-1"
    updated.dify_uploaded_at = datetime.now(UTC)
    updated.dify_sync_status = "synced"
    updated.note = "Dify file uploaded: dify-file-1"

    monkeypatch.setattr(service.document_repo, "get_by_id", lambda *_: doc)
    monkeypatch.setattr(service, "_resolve_local_path", lambda *_: Path("/tmp/doc.txt"))
    async def fake_upload_file(*_args, **_kwargs):
        return DifyUploadedFile(
            file_id="dify-file-1",
            name="doc.txt",
            size=3,
            extension="txt",
            mime_type="text/plain",
            created_at=1,
        )

    monkeypatch.setattr(service.dify_client, "upload_file", fake_upload_file)

    monkeypatch.setattr(service.document_repo, "mark_dify_syncing", lambda *args, **kwargs: doc)
    monkeypatch.setattr(service.document_repo, "mark_dify_synced", lambda *args, **kwargs: updated)

    payload = asyncio.run(service.trigger_dify_index(db, doc_id=doc.id))

    assert payload["target_system"] == "dify"
    assert payload["status"] == DocumentStatus.SYNCED.value
    assert payload["message"] == "Dify file uploaded: dify-file-1"
    assert db.commits == 1


def test_trigger_dify_index_marks_failed_when_local_file_is_missing(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    doc = _doc(DocumentStatus.UPLOADED.value)
    failed = _doc(DocumentStatus.FAILED.value)
    failed.dify_sync_status = "failed"
    failed.dify_error_code = "local_file_missing"
    failed.dify_error_message = "Local document file does not exist"
    failed.note = "Local document file does not exist"

    monkeypatch.setattr(service.document_repo, "get_by_id", lambda *_: doc)
    monkeypatch.setattr(service.document_repo, "mark_dify_failed", lambda *args, **kwargs: failed)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.trigger_dify_index(db, doc_id=doc.id))

    assert exc.value.status_code == 404
    assert exc.value.detail == "Local document file does not exist"
    assert db.commits == 1


def test_trigger_dify_index_maps_file_too_large_error(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    doc = _doc(DocumentStatus.UPLOADED.value)
    failed = _doc(DocumentStatus.FAILED.value)
    failed.dify_sync_status = "failed"
    failed.dify_error_code = "file_too_large"
    failed.dify_error_message = "Dify rejected the file as too large"
    failed.note = "Dify rejected the file as too large"

    monkeypatch.setattr(service.document_repo, "get_by_id", lambda *_: doc)
    monkeypatch.setattr(service, "_resolve_local_path", lambda *_: Path("/tmp/doc.txt"))
    monkeypatch.setattr(service.document_repo, "mark_dify_syncing", lambda *args, **kwargs: doc)
    monkeypatch.setattr(service.document_repo, "mark_dify_failed", lambda *args, **kwargs: failed)

    async def fake_upload_file(*_args, **_kwargs):
        raise DifyFileTooLargeError("too large", error_code="file_too_large")

    monkeypatch.setattr(service.dify_client, "upload_file", fake_upload_file)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.trigger_dify_index(db, doc_id=doc.id))

    assert exc.value.status_code == 400
    assert exc.value.detail == "Dify rejected the file as too large"
    assert db.commits == 1


def test_trigger_dify_index_maps_unsupported_file_type_error(monkeypatch):
    service = AdminDocumentService()
    db = DummyDB()
    doc = _doc(DocumentStatus.UPLOADED.value)
    failed = _doc(DocumentStatus.FAILED.value)
    failed.dify_sync_status = "failed"
    failed.dify_error_code = "unsupported_file_type"
    failed.dify_error_message = "Dify does not support this file type"
    failed.note = "Dify does not support this file type"

    monkeypatch.setattr(service.document_repo, "get_by_id", lambda *_: doc)
    monkeypatch.setattr(service, "_resolve_local_path", lambda *_: Path("/tmp/doc.txt"))
    monkeypatch.setattr(service.document_repo, "mark_dify_syncing", lambda *args, **kwargs: doc)
    monkeypatch.setattr(service.document_repo, "mark_dify_failed", lambda *args, **kwargs: failed)

    async def fake_upload_file(*_args, **_kwargs):
        raise DifyUnsupportedFileTypeError("bad type", error_code="unsupported_file_type")

    monkeypatch.setattr(service.dify_client, "upload_file", fake_upload_file)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.trigger_dify_index(db, doc_id=doc.id))

    assert exc.value.status_code == 400
    assert exc.value.detail == "Dify does not support this file type"
    assert db.commits == 1
