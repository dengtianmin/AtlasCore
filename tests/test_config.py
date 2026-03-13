from app.core.config import Settings


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
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
    assert settings.JWT_SECRET is None
    assert settings.DATABASE_URL is None
    assert settings.NEO4J_URI is None
    assert settings.NEO4J_USERNAME is None
    assert settings.NEO4J_PASSWORD is None
    assert settings.DIFY_BASE_URL is None
    assert settings.DIFY_API_KEY is None


def test_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("APP_NAME", "AtlasCore API Test")
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("JWT_SECRET", "local-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/atlascore")
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
    assert settings.JWT_SECRET == "local-secret"
    assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/atlascore"
    assert settings.NEO4J_URI == "neo4j+s://demo.databases.neo4j.io"
    assert settings.NEO4J_USERNAME == "neo4j"
    assert settings.NEO4J_PASSWORD == "password"
    assert settings.DIFY_BASE_URL == "https://dify.example.com"
    assert settings.DIFY_API_KEY == "dify-api-key"


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
