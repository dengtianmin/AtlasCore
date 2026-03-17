import json
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.secrets import SecretResolutionError


@pytest.fixture(autouse=True)
def _isolate_settings_sources(monkeypatch):
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for key in [
        "APP_NAME",
        "APP_ENV",
        "PORT",
        "LOG_LEVEL",
        "APP_CONFIG_PATH",
        "SQLITE_PATH",
        "CSV_EXPORT_DIR",
        "GRAPH_ENABLED",
        "GRAPH_DEFAULT_LIMIT",
        "GRAPH_MAX_NEIGHBORS",
        "GRAPH_RELOAD_ON_START",
        "GRAPH_EXPORT_DIR",
        "GRAPH_IMPORT_DIR",
        "GRAPH_SNAPSHOT_PATH",
        "GRAPH_INSTANCE_LOCAL_PATH",
        "GRAPH_INSTANCE_ID",
        "GRAPH_DB_VERSION",
        "KEY_VAULT_ENABLED",
        "KEY_VAULT_URL",
        "AZURE_KEY_VAULT_URL",
        "KEY_VAULT_USE_MANAGED_IDENTITY",
        "KEY_VAULT_TIMEOUT_SECONDS",
        "JWT_SECRET",
        "JWT_SECRET_NAME",
        "INITIAL_ADMIN_USERNAME",
        "INITIAL_ADMIN_PASSWORD",
        "INITIAL_ADMIN_PASSWORD_SECRET_NAME",
        "ADMIN_AUTH_SECRET",
        "ADMIN_AUTH_SECRET_NAME",
        "ADMIN_PASSWORD_HASH",
        "ADMIN_PASSWORD_HASH_SECRET_NAME",
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
        "DIFY_BASE_URL",
        "DIFY_API_BASE",
        "DIFY_API_KEY",
        "DIFY_API_KEY_SECRET_NAME",
        "DIFY_WORKFLOW_ID",
        "DIFY_RESPONSE_MODE",
        "DIFY_TEXT_INPUT_VARIABLE",
        "DIFY_FILE_INPUT_VARIABLE",
        "DIFY_ENABLE_TRACE",
        "DIFY_USER_PREFIX",
        "DIFY_DEBUG_LOG_PATH",
        "GRAPH_EXTRACTION_PROMPT",
        "GRAPH_EXTRACTION_MODEL_PROVIDER",
        "GRAPH_EXTRACTION_MODEL_NAME",
        "GRAPH_EXTRACTION_MODEL_API_BASE_URL",
        "GRAPH_EXTRACTION_MODEL_API_KEY",
        "GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME",
        "GRAPH_EXTRACTION_MODEL_ENABLED",
        "GRAPH_EXTRACTION_MODEL_THINKING_ENABLED",
        "GRAPH_EXTRACTION_MODEL_TIMEOUT_SECONDS",
        "DOCUMENT_LOCAL_STORAGE_DIR",
        "DOCUMENT_MAX_FILE_SIZE_BYTES",
        "DOCUMENT_ALLOWED_EXTENSIONS",
        "DOCUMENT_ALLOWED_MIME_TYPES",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_settings_defaults(monkeypatch):
    settings = Settings()

    assert settings.APP_NAME == "AtlasCore API"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.APP_ENV == "development"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000
    assert settings.LOG_LEVEL == "INFO"
    assert settings.APP_CONFIG_PATH is None
    assert settings.SQLITE_PATH == "./data/atlascore.db"
    assert settings.CSV_EXPORT_DIR == "./data/exports"
    assert settings.GRAPH_ENABLED is True
    assert settings.GRAPH_DEFAULT_LIMIT == 100
    assert settings.GRAPH_MAX_NEIGHBORS == 200
    assert settings.GRAPH_RELOAD_ON_START is True
    assert settings.GRAPH_EXPORT_DIR == "./data/graph_exports"
    assert settings.GRAPH_IMPORT_DIR == "./data/graph_imports"
    assert settings.graph_instance_path.name == "atlascore_graph.db"
    assert settings.KEY_VAULT_ENABLED is False
    assert settings.KEY_VAULT_URL is None
    assert settings.AZURE_KEY_VAULT_URL is None
    assert settings.KEY_VAULT_USE_MANAGED_IDENTITY is False
    assert settings.JWT_SECRET is None
    assert settings.JWT_SECRET_NAME is None
    assert settings.INITIAL_ADMIN_PASSWORD is None
    assert settings.ADMIN_AUTH_SECRET is None
    assert settings.ADMIN_PASSWORD_HASH is None
    assert settings.NEO4J_URI is None
    assert settings.NEO4J_USERNAME is None
    assert settings.NEO4J_PASSWORD is None
    assert settings.DIFY_BASE_URL is None
    assert settings.DIFY_API_KEY is None
    assert settings.DIFY_WORKFLOW_ID is None
    assert settings.DIFY_RESPONSE_MODE == "blocking"
    assert settings.DIFY_TEXT_INPUT_VARIABLE is None
    assert settings.DIFY_FILE_INPUT_VARIABLE is None
    assert settings.DIFY_ENABLE_TRACE is False
    assert settings.DIFY_USER_PREFIX == "guest"
    assert settings.DIFY_DEBUG_LOG_PATH == "./data/dify_debug.jsonl"
    assert settings.GRAPH_EXTRACTION_PROMPT is None
    assert settings.GRAPH_EXTRACTION_MODEL_PROVIDER == "openai-compatible"
    assert settings.GRAPH_EXTRACTION_MODEL_NAME is None
    assert settings.GRAPH_EXTRACTION_MODEL_API_BASE_URL is None
    assert settings.GRAPH_EXTRACTION_MODEL_API_KEY is None
    assert settings.GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME is None
    assert settings.GRAPH_EXTRACTION_MODEL_ENABLED is False
    assert settings.GRAPH_EXTRACTION_MODEL_THINKING_ENABLED is True
    assert settings.GRAPH_EXTRACTION_MODEL_TIMEOUT_SECONDS == 120.0
    assert settings.PAGE_DEFAULTS == {}
    assert settings.FEATURE_FLAGS == {}
    assert settings.EXPORT_RULES == {}
    assert settings.FIXED_MAPPINGS == {}


def test_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("APP_NAME", "AtlasCore API Test")
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("SQLITE_PATH", "/tmp/atlascore.db")
    monkeypatch.setenv("CSV_EXPORT_DIR", "/tmp/exports")
    monkeypatch.setenv("GRAPH_ENABLED", "false")
    monkeypatch.setenv("GRAPH_DEFAULT_LIMIT", "80")
    monkeypatch.setenv("GRAPH_MAX_NEIGHBORS", "160")
    monkeypatch.setenv("GRAPH_RELOAD_ON_START", "false")
    monkeypatch.setenv("GRAPH_EXPORT_DIR", "/tmp/graph_exports")
    monkeypatch.setenv("GRAPH_IMPORT_DIR", "/tmp/graph_imports")
    monkeypatch.setenv("GRAPH_INSTANCE_LOCAL_PATH", "/tmp/graph_instance.db")
    monkeypatch.setenv("GRAPH_INSTANCE_ID", "instance-a")
    monkeypatch.setenv("GRAPH_DB_VERSION", "20260317")
    monkeypatch.setenv("KEY_VAULT_ENABLED", "true")
    monkeypatch.setenv("KEY_VAULT_URL", "https://atlascore-kv.vault.azure.net")
    monkeypatch.setenv("KEY_VAULT_USE_MANAGED_IDENTITY", "true")
    monkeypatch.setenv("KEY_VAULT_TIMEOUT_SECONDS", "9")
    monkeypatch.setenv("JWT_SECRET", "local-secret")
    monkeypatch.setenv("JWT_SECRET_NAME", "jwt-secret")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD_SECRET_NAME", "initial-admin-password")
    monkeypatch.setenv("ADMIN_AUTH_SECRET", "admin-auth")
    monkeypatch.setenv("ADMIN_AUTH_SECRET_NAME", "admin-auth-secret")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "bcrypt-hash")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH_SECRET_NAME", "admin-password-hash")
    monkeypatch.setenv("NEO4J_URI", "neo4j+s://demo.databases.neo4j.io")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setenv("DIFY_API_KEY", "dify-api-key")
    monkeypatch.setenv("DIFY_API_KEY_SECRET_NAME", "dify-api-key")
    monkeypatch.setenv("DIFY_WORKFLOW_ID", "workflow-1")
    monkeypatch.setenv("DIFY_RESPONSE_MODE", "blocking")
    monkeypatch.setenv("DIFY_TEXT_INPUT_VARIABLE", "question")
    monkeypatch.setenv("DIFY_FILE_INPUT_VARIABLE", "attachments")
    monkeypatch.setenv("DIFY_ENABLE_TRACE", "true")
    monkeypatch.setenv("DIFY_USER_PREFIX", "atlas")
    monkeypatch.setenv("DIFY_DEBUG_LOG_PATH", "/tmp/dify-debug.jsonl")
    monkeypatch.setenv("GRAPH_EXTRACTION_PROMPT", "extract prompt")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_PROVIDER", "openai-compatible")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_NAME", "gpt-4o-mini")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_API_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_API_KEY", "graph-api-key")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME", "graph-model-api-key")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_ENABLED", "true")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_THINKING_ENABLED", "false")
    monkeypatch.setenv("GRAPH_EXTRACTION_MODEL_TIMEOUT_SECONDS", "180")

    settings = Settings()

    assert settings.APP_NAME == "AtlasCore API Test"
    assert settings.APP_ENV == "staging"
    assert settings.PORT == 9000
    assert settings.LOG_LEVEL == "WARNING"
    assert settings.SQLITE_PATH == "/tmp/atlascore.db"
    assert settings.CSV_EXPORT_DIR == "/tmp/exports"
    assert settings.GRAPH_ENABLED is False
    assert settings.GRAPH_DEFAULT_LIMIT == 80
    assert settings.GRAPH_MAX_NEIGHBORS == 160
    assert settings.GRAPH_RELOAD_ON_START is False
    assert settings.GRAPH_EXPORT_DIR == "/tmp/graph_exports"
    assert settings.GRAPH_IMPORT_DIR == "/tmp/graph_imports"
    assert str(settings.graph_instance_path) == "/tmp/graph_instance.db"
    assert settings.GRAPH_INSTANCE_ID == "instance-a"
    assert settings.GRAPH_DB_VERSION == "20260317"
    assert settings.KEY_VAULT_ENABLED is True
    assert settings.KEY_VAULT_URL == "https://atlascore-kv.vault.azure.net"
    assert settings.KEY_VAULT_USE_MANAGED_IDENTITY is True
    assert settings.KEY_VAULT_TIMEOUT_SECONDS == 9
    assert settings.JWT_SECRET == "local-secret"
    assert settings.JWT_SECRET_NAME == "jwt-secret"
    assert settings.INITIAL_ADMIN_PASSWORD == "admin-secret"
    assert settings.INITIAL_ADMIN_PASSWORD_SECRET_NAME == "initial-admin-password"
    assert settings.ADMIN_AUTH_SECRET == "admin-auth"
    assert settings.ADMIN_AUTH_SECRET_NAME == "admin-auth-secret"
    assert settings.ADMIN_PASSWORD_HASH == "bcrypt-hash"
    assert settings.ADMIN_PASSWORD_HASH_SECRET_NAME == "admin-password-hash"
    assert settings.NEO4J_URI == "neo4j+s://demo.databases.neo4j.io"
    assert settings.NEO4J_USERNAME == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.DIFY_BASE_URL == "https://dify.example.com"
    assert settings.DIFY_API_KEY == "dify-api-key"
    assert settings.DIFY_API_KEY_SECRET_NAME == "dify-api-key"
    assert settings.DIFY_WORKFLOW_ID == "workflow-1"
    assert settings.DIFY_RESPONSE_MODE == "blocking"
    assert settings.DIFY_TEXT_INPUT_VARIABLE == "question"
    assert settings.DIFY_FILE_INPUT_VARIABLE == "attachments"
    assert settings.DIFY_ENABLE_TRACE is True
    assert settings.DIFY_USER_PREFIX == "atlas"
    assert settings.DIFY_DEBUG_LOG_PATH == "/tmp/dify-debug.jsonl"
    assert settings.GRAPH_EXTRACTION_PROMPT == "extract prompt"
    assert settings.GRAPH_EXTRACTION_MODEL_PROVIDER == "openai-compatible"
    assert settings.GRAPH_EXTRACTION_MODEL_NAME == "gpt-4o-mini"
    assert settings.GRAPH_EXTRACTION_MODEL_API_BASE_URL == "https://api.openai.com/v1"
    assert settings.GRAPH_EXTRACTION_MODEL_API_KEY == "graph-api-key"
    assert settings.GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME == "graph-model-api-key"
    assert settings.GRAPH_EXTRACTION_MODEL_ENABLED is True
    assert settings.GRAPH_EXTRACTION_MODEL_THINKING_ENABLED is False
    assert settings.GRAPH_EXTRACTION_MODEL_TIMEOUT_SECONDS == 180


def test_settings_reads_yaml_config_file(monkeypatch, tmp_path):
    config_path = tmp_path / "app.yaml"
    config_path.write_text(
        "\n".join(
            [
                "app:",
                "  name: AtlasCore YAML",
                "  port: 8010",
                "admin:",
                "  initial_username: atlas-admin",
                "defaults:",
                "  page:",
                "    admin_dashboard_size: 20",
                "  features:",
                "    enable_debug_endpoints: true",
                "    graph_reload_on_start: false",
                "export:",
                "  rules:",
                "    qa_logs:",
                '      delimiter: ";"',
                "graph:",
                "  default_limit: 120",
                "  max_neighbors: 240",
                "  export_dir: ./yaml-graph-exports",
                "integrations:",
                "  neo4j:",
                "    enabled: false",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("APP_CONFIG_PATH", str(config_path))

    settings = Settings()

    assert settings.APP_NAME == "AtlasCore YAML"
    assert settings.PORT == 8010
    assert settings.INITIAL_ADMIN_USERNAME == "atlas-admin"
    assert settings.PAGE_DEFAULTS == {"admin_dashboard_size": 20}
    assert settings.FEATURE_FLAGS == {"enable_debug_endpoints": True, "graph_reload_on_start": False}
    assert settings.GRAPH_RELOAD_ON_START is False
    assert settings.GRAPH_DEFAULT_LIMIT == 120
    assert settings.GRAPH_MAX_NEIGHBORS == 240
    assert settings.GRAPH_EXPORT_DIR == "./yaml-graph-exports"
    assert settings.EXPORT_RULES == {"qa_logs": {"delimiter": ";"}}
    assert settings.RESERVED_INTEGRATIONS == {"neo4j": {"enabled": False}}


def test_settings_reads_json_config_file_and_env_overrides(monkeypatch, tmp_path):
    config_path = tmp_path / "app.json"
    config_path.write_text(
        json.dumps(
            {
                "app": {"name": "AtlasCore JSON", "port": 8012},
                "admin": {"initial_username": "json-admin"},
                "defaults": {"features": {"enable_csv_export": True}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("APP_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("APP_NAME", "AtlasCore Env Override")

    settings = Settings()

    assert settings.APP_NAME == "AtlasCore Env Override"
    assert settings.PORT == 8012
    assert settings.INITIAL_ADMIN_USERNAME == "json-admin"
    assert settings.FEATURE_FLAGS == {"enable_csv_export": True}


def test_settings_accepts_dify_api_base_alias(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DIFY_API_BASE", "https://dify-alias.example.com")
    monkeypatch.setenv("DIFY_API_KEY", "alias-key")

    settings = Settings()

    assert settings.DIFY_BASE_URL == "https://dify-alias.example.com"
    assert settings.is_dify_configured() is True


def test_runtime_directories_are_created(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "unit-test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "StrongPass123!")
    monkeypatch.setenv("APP_CONFIG_PATH", "")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "db" / "atlascore.db"))
    monkeypatch.setenv("CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setenv("GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setenv("GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "graph.db"))

    settings = Settings()
    summary = settings.runtime_config_summary()

    assert summary["paths"]["sqlite_path"]["parent_exists"] is True
    assert summary["paths"]["csv_export_dir"]["exists"] is True
    assert summary["paths"]["graph_export_dir"]["exists"] is True
    assert summary["paths"]["graph_import_dir"]["exists"] is True
    assert summary["paths"]["graph_instance_local_path"]["parent_exists"] is True
    assert summary["dify_configured"] is False
    assert summary["admin_auth_configured"] is False
    assert summary["graph_extraction_model_timeout_seconds"] == 120.0


def test_production_requires_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    try:
        Settings()
        raised = False
    except ValueError as exc:
        raised = True
        assert "JWT_SECRET is required" in str(exc)

    assert raised is True


def test_invalid_config_path_raises_value_error(monkeypatch):
    monkeypatch.setenv("APP_CONFIG_PATH", "/tmp/does-not-exist.yaml")

    with pytest.raises(ValueError, match="APP_CONFIG_PATH does not exist"):
        Settings()


def test_settings_resolve_secrets_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "env-jwt-secret")
    monkeypatch.setenv("DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setenv("DIFY_API_KEY", "env-dify-api-key")

    settings = Settings()

    assert settings.resolved_jwt_secret == "env-jwt-secret"
    assert settings.resolved_dify_api_key == "env-dify-api-key"
    summary = settings.secret_status_summary()
    assert summary["JWT_SECRET"] == {"configured": True, "source": "env"}
    assert summary["DIFY_API_KEY"] == {"configured": True, "source": "env"}


def test_settings_resolve_secrets_from_key_vault_secret_name(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("KEY_VAULT_ENABLED", "true")
    monkeypatch.setenv("KEY_VAULT_URL", "https://atlascore-kv.vault.azure.net")
    monkeypatch.setenv("JWT_SECRET_NAME", "jwt-secret")

    settings = Settings()

    class MockSecretClient:
        def get_secret(self, name: str):
            assert name == "jwt-secret"
            return SimpleNamespace(value="kv-jwt-secret")

    mock_client = MockSecretClient()
    monkeypatch.setattr(
        "app.core.secrets.SecretResolver._get_secret_client",
        lambda self, vault_url: mock_client,
    )

    resolved = settings.resolve_secret(
        env_var="JWT_SECRET",
        secret_name_var="JWT_SECRET_NAME",
        required=True,
        allow_missing_in_dev=False,
    )

    assert resolved.value == "kv-jwt-secret"
    assert resolved.source == "key_vault_sdk"


def test_settings_resolve_secrets_from_key_vault_reference(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv(
        "JWT_SECRET",
        "@Microsoft.KeyVault(VaultName=atlascore-kv;SecretName=jwt-secret)",
    )

    settings = Settings()

    class MockSecretClient:
        def get_secret(self, name: str):
            assert name == "jwt-secret"
            return SimpleNamespace(value="kv-ref-secret")

    monkeypatch.setattr(
        "app.core.secrets.SecretResolver._get_secret_client",
        lambda self, vault_url: MockSecretClient(),
    )

    resolved = settings.resolve_secret(env_var="JWT_SECRET", secret_name_var="JWT_SECRET_NAME")

    assert resolved.value == "kv-ref-secret"
    assert resolved.source == "kv_reference"


def test_settings_allow_missing_secret_in_test_when_sdk_unavailable(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("KEY_VAULT_ENABLED", "true")
    monkeypatch.setenv("KEY_VAULT_URL", "https://atlascore-kv.vault.azure.net")
    monkeypatch.setenv("JWT_SECRET_NAME", "jwt-secret")

    settings = Settings()
    monkeypatch.setattr(
        "app.core.secrets.SecretResolver._get_secret_client",
        lambda self, vault_url: (_ for _ in ()).throw(SecretResolutionError("sdk unavailable")),
    )

    resolved = settings.resolve_secret(env_var="JWT_SECRET", secret_name_var="JWT_SECRET_NAME")

    assert resolved.value is None
    assert resolved.source == "missing"


def test_settings_require_secret_in_production_when_key_vault_fails(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("KEY_VAULT_ENABLED", "true")
    monkeypatch.setenv("KEY_VAULT_URL", "https://atlascore-kv.vault.azure.net")
    monkeypatch.setenv("JWT_SECRET_NAME", "jwt-secret")

    monkeypatch.setattr(
        "app.core.secrets.SecretResolver._get_secret_client",
        lambda self, vault_url: (_ for _ in ()).throw(SecretResolutionError("sdk unavailable")),
    )

    with pytest.raises(ValueError, match="JWT_SECRET is required but was not resolved"):
        Settings()


def test_secret_status_summary_does_not_include_secret_values(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "super-secret-value")

    settings = Settings()
    summary = settings.secret_status_summary()

    assert "super-secret-value" not in json.dumps(summary)
    assert summary["JWT_SECRET"]["configured"] is True


def test_non_secret_graph_configuration_remains_unchanged(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("GRAPH_DEFAULT_LIMIT", "55")
    monkeypatch.setenv("GRAPH_IMPORT_DIR", "/tmp/imports")

    settings = Settings()

    assert settings.GRAPH_DEFAULT_LIMIT == 55
    assert settings.GRAPH_IMPORT_DIR == "/tmp/imports"
