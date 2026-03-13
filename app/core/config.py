from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AtlasCore API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    PORT: int = Field(default=8000, ge=1, le=65535)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    JWT_SECRET: str | None = None
    DATABASE_URL: str | None = None
    NEO4J_URI: str | None = None
    NEO4J_USERNAME: str | None = None
    NEO4J_PASSWORD: str | None = None
    DIFY_BASE_URL: str | None = None
    DIFY_API_KEY: str | None = None
    DOCUMENT_LOCAL_STORAGE_DIR: str = "./data/uploads"

    API_V1_PREFIX: str = ""
    HOST: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_debug(self) -> bool:
        return self.APP_ENV in {"development", "test"}

    @model_validator(mode="after")
    def validate_critical_config(self) -> "Settings":
        if self.is_production and not self.JWT_SECRET:
            raise ValueError("JWT_SECRET is required when APP_ENV=production")

        neo4j_values = [self.NEO4J_URI, self.NEO4J_USERNAME, self.NEO4J_PASSWORD]
        if any(neo4j_values) and not all(neo4j_values):
            raise ValueError(
                "NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be provided together"
            )

        dify_values = [self.DIFY_BASE_URL, self.DIFY_API_KEY]
        if any(dify_values) and not all(dify_values):
            raise ValueError("DIFY_BASE_URL and DIFY_API_KEY must be provided together")

        return self


settings = Settings()
