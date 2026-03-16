import io
import json

from urllib import error

from app.core.config import settings
from app.integrations.dify.client import DifyClient
from app.integrations.dify.exceptions import DifyConfigurationError, DifyRequestError
from app.integrations.dify.schemas import DifyChatRequest, DifyDocumentIndexRequest


class _MockHttpResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


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


def test_dify_client_supports_blocking_chat(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def _mock_urlopen(req, timeout):
        assert req.full_url == "https://dify.example.com/v1/chat-messages"
        assert timeout == settings.DIFY_TIMEOUT_SECONDS
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["query"] == "hello"
        return _MockHttpResponse(
            {
                "answer": "world",
                "conversation_id": "session-1",
                "message_id": "msg-1",
                "metadata": {
                    "retriever_resources": [
                        {
                            "document_name": "doc-1",
                            "content": "context line",
                            "data_source_type": "knowledge",
                        }
                    ],
                    "usage": {"total_tokens": 12},
                },
            }
        )

    monkeypatch.setattr("app.integrations.dify.client.request.urlopen", _mock_urlopen)
    client = DifyClient()
    res = client.chat(DifyChatRequest(query="hello", session_id="session-1"))

    assert client.is_enabled() is True
    assert res.answer == "world"
    assert res.retrieved_context == "context line"
    assert res.sources[0].title == "doc-1"
    assert res.provider_message_id == "msg-1"
    assert res.metadata["total_tokens"] == 12


def test_dify_client_raises_when_chat_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY", None)

    client = DifyClient()

    try:
        client.chat(DifyChatRequest(query="hello", session_id="session-1"))
    except DifyConfigurationError:
        pass
    else:
        raise AssertionError("Expected DifyConfigurationError when chat is not configured")


def test_dify_client_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", "api-key")
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    def _mock_urlopen(req, timeout):
        raise error.HTTPError(
            url=req.full_url,
            code=500,
            msg="server error",
            hdrs=None,
            fp=io.BytesIO(b'{"message":"failed"}'),
        )

    monkeypatch.setattr("app.integrations.dify.client.request.urlopen", _mock_urlopen)
    client = DifyClient()

    try:
        client.chat(DifyChatRequest(query="hello", session_id="session-1"))
    except DifyRequestError as exc:
        assert "status 500" in str(exc)
    else:
        raise AssertionError("Expected DifyRequestError for HTTP failures")


def test_dify_client_supports_key_vault_secret_name(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "KEY_VAULT_ENABLED", True)
    monkeypatch.setattr(settings, "KEY_VAULT_URL", "https://atlascore-kv.vault.azure.net")
    monkeypatch.setattr(settings, "DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setattr(settings, "DIFY_API_KEY", None)
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", "dify-api-key")
    monkeypatch.setattr(
        "app.core.secrets.SecretResolver._get_secret_client",
        lambda self, vault_url: type(
            "MockSecretClient",
            (),
            {"get_secret": lambda self, name: type("SecretBundle", (), {"value": "api-key"})()},
        )(),
    )

    client = DifyClient()

    assert client.is_enabled() is True
