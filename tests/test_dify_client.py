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
    monkeypatch.setattr(settings, "DIFY_API_KEY_SECRET_NAME", None)

    client = DifyClient()
    res = client.enqueue_document_index(
        DifyDocumentIndexRequest(document_id="doc-2", title="Doc 2")
    )

    assert client.is_enabled() is True
    assert res.status == "queued"
    assert res.job_id.startswith("dify-")


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
