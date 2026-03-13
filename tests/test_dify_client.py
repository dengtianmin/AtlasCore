from app.core.config import settings
from app.integrations.dify.client import DifyClient
from app.integrations.dify.schemas import DifyDocumentIndexRequest


def test_dify_client_returns_placeholder_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY", None)

    client = DifyClient()
    res = client.enqueue_document_index(
        DifyDocumentIndexRequest(document_id="doc-1", title="Doc 1", source_uri="/tmp/doc")
    )

    assert client.is_enabled() is False
    assert res.status == "queued"
    assert res.job_id == "placeholder-doc-1"


def test_dify_client_returns_staged_response_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")

    client = DifyClient()
    res = client.enqueue_document_index(
        DifyDocumentIndexRequest(document_id="doc-2", title="Doc 2")
    )

    assert client.is_enabled() is True
    assert res.status == "queued"
    assert res.job_id.startswith("dify-")
