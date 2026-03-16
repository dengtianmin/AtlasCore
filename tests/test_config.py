import json

import pytest

from app.core.config import Settings


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
    monkeypatch.delenv("SQLITE_PATH", raising=False)
    monkeypatch.delenv("CSV_EXPORT_DIR", raising=False)
    monkeypatch.delenv("GRAPH_ENABLED", raising=False)
    monkeypatch.delenv("GRAPH_DEFAULT_LIMIT", raising=False)
    monkeypatch.delenv("GRAPH_MAX_NEIGHBORS", raising=False)
    monkeypatch.delenv("GRAPH_RELOAD_ON_START", raising=False)
    monkeypatch.delenv("GRAPH_EXPORT_DIR", raising=False)
    monkeypatch.delenv("GRAPH_IMPORT_DIR", raising=False)
    monkeypatch.delenv("GRAPH_SNAPSHOT_PATH", raising=False)
    monkeypatch.delenv("GRAPH_INSTANCE_LOCAL_PATH", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("INITIAL_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USERNAME", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    monkeypatch.delenv("DIFY_BASE_URL", raising=False)
    monkeypatch.delenv("DIFY_API_KEY", raising=False)

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
    assert settings.JWT_SECRET is None
    assert settings.INITIAL_ADMIN_PASSWORD is None
    assert settings.NEO4J_URI is None
    assert settings.NEO4J_USERNAME is None
    assert settings.NEO4J_PASSWORD is None
    assert settings.DIFY_BASE_URL is None
    assert settings.DIFY_API_KEY is None
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
    monkeypatch.setenv("JWT_SECRET", "local-secret")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setenv("NEO4J_URI", "neo4j+s://demo.databases.neo4j.io")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("DIFY_BASE_URL", "https://dify.example.com")
    monkeypatch.setenv("DIFY_API_KEY", "dify-api-key")

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
    assert settings.JWT_SECRET == "local-secret"
    assert settings.INITIAL_ADMIN_PASSWORD == "admin-secret"
    assert settings.NEO4J_URI == "neo4j+s://demo.databases.neo4j.io"
    assert settings.NEO4J_USERNAME == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.DIFY_BASE_URL == "https://dify.example.com"
    assert settings.DIFY_API_KEY == "dify-api-key"


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
                "export:",
                "  rules:",
                "    qa_logs:",
                '      delimiter: ";"',
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
    assert settings.FEATURE_FLAGS == {"enable_debug_endpoints": True}
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


def test_production_requires_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    try:
        Settings()
        raised = False
    except ValueError as exc:
        raised = True
        assert "JWT_SECRET is required when APP_ENV=production" in str(exc)

    assert raised is True


def test_invalid_config_path_raises_value_error(monkeypatch):
    monkeypatch.setenv("APP_CONFIG_PATH", "/tmp/does-not-exist.yaml")

    with pytest.raises(ValueError, match="APP_CONFIG_PATH does not exist"):
        Settings()
