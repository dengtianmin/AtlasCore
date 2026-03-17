from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.admin import DocumentListResponse


def test_document_list_response_accepts_graph_extraction_statuses():
    now = datetime.now(UTC)
    payload = {
        "items": [
            {
                "id": uuid4(),
                "filename": "knowledge.md",
                "file_type": "md",
                "status": "pending_extraction",
                "source_type": "upload",
                "uploaded_at": now,
                "synced_to_dify": False,
                "synced_to_graph": False,
                "note": None,
                "local_path": "/tmp/knowledge.md",
                "source_uri": "/tmp/knowledge.md",
                "mime_type": "text/markdown",
                "content_type": "text/markdown",
                "file_size": 128,
                "file_extension": "md",
                "dify_upload_file_id": None,
                "dify_uploaded_at": None,
                "dify_sync_status": "not_synced",
                "dify_error_code": None,
                "dify_error_message": None,
                "created_by": None,
                "created_at": now,
                "last_sync_target": None,
                "last_sync_status": None,
                "last_sync_at": None,
                "removed_from_graph_at": None,
                "invalidated_at": None,
                "is_active": True,
                "extraction_task_id": None,
                "dify_file_input_variable": None,
                "dify_workflow_file_input": None,
            },
            {
                "id": uuid4(),
                "filename": "knowledge-2.md",
                "file_type": "md",
                "status": "extraction_failed",
                "source_type": "upload",
                "uploaded_at": now,
                "synced_to_dify": False,
                "synced_to_graph": False,
                "note": "model config missing",
                "local_path": "/tmp/knowledge-2.md",
                "source_uri": "/tmp/knowledge-2.md",
                "mime_type": "text/markdown",
                "content_type": "text/markdown",
                "file_size": 256,
                "file_extension": "md",
                "dify_upload_file_id": None,
                "dify_uploaded_at": None,
                "dify_sync_status": "not_synced",
                "dify_error_code": None,
                "dify_error_message": None,
                "created_by": None,
                "created_at": now,
                "last_sync_target": "graph",
                "last_sync_status": "extraction_failed",
                "last_sync_at": now,
                "removed_from_graph_at": None,
                "invalidated_at": None,
                "is_active": True,
                "extraction_task_id": None,
                "dify_file_input_variable": None,
                "dify_workflow_file_input": None,
            },
        ]
    }

    response = DocumentListResponse(**payload)

    assert response.items[0].status.value == "pending_extraction"
    assert response.items[1].status.value == "extraction_failed"
