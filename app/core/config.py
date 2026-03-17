import json
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from app.core.secrets import ResolvedSecret, SecretResolutionError, SecretResolver


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_config_file(path_value: str | None) -> dict[str, Any]:
    if not path_value:
        return {}

    path = Path(path_value).expanduser()
    if not path.exists():
        raise ValueError(f"APP_CONFIG_PATH does not exist: {path}")

    suffix = path.suffix.lower()
    raw_text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        payload = json.loads(raw_text)
    elif suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(raw_text) or {}
    else:
        raise ValueError("APP_CONFIG_PATH must point to a .json, .yaml, or .yml file")

    if not isinstance(payload, dict):
        raise ValueError("Config file root must be a JSON/YAML object")

    return payload


class Settings(BaseSettings):
    APP_NAME: str = "AtlasCore API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    PORT: int = Field(default=8000, ge=1, le=65535)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    APP_CONFIG_PATH: str | None = None
    SQLITE_PATH: str = "./data/atlascore.db"
    CSV_EXPORT_DIR: str = "./data/exports"
    GRAPH_ENABLED: bool = True
    GRAPH_DEFAULT_LIMIT: int = Field(default=100, ge=1, le=1000)
    GRAPH_MAX_NEIGHBORS: int = Field(default=200, ge=1, le=5000)
    GRAPH_RELOAD_ON_START: bool = True
    GRAPH_EXPORT_DIR: str = "./data/graph_exports"
    GRAPH_IMPORT_DIR: str = "./data/graph_imports"
    GRAPH_SNAPSHOT_PATH: str | None = None
    GRAPH_INSTANCE_LOCAL_PATH: str | None = None
    GRAPH_INSTANCE_ID: str = "local"
    GRAPH_DB_VERSION: str | None = None
    KEY_VAULT_ENABLED: bool = False
    KEY_VAULT_URL: str | None = None
    AZURE_KEY_VAULT_URL: str | None = None
    KEY_VAULT_USE_MANAGED_IDENTITY: bool = False
    KEY_VAULT_TIMEOUT_SECONDS: float = Field(default=5.0, gt=0)

    JWT_SECRET: str | None = None
    JWT_SECRET_NAME: str | None = None
    INITIAL_ADMIN_PASSWORD: str | None = None
    INITIAL_ADMIN_PASSWORD_SECRET_NAME: str | None = None
    ADMIN_AUTH_SECRET: str | None = None
    ADMIN_AUTH_SECRET_NAME: str | None = None
    ADMIN_PASSWORD_HASH: str | None = None
    ADMIN_PASSWORD_HASH_SECRET_NAME: str | None = None
    NEO4J_URI: str | None = None
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_USERNAME: str | None = None
    NEO4J_PASSWORD: str | None = None
    DIFY_BASE_URL: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DIFY_BASE_URL", "DIFY_API_BASE"),
    )
    DIFY_API_KEY: str | None = None
    DIFY_API_KEY_SECRET_NAME: str | None = None
    DIFY_TIMEOUT_SECONDS: float = Field(default=15.0, gt=0)
    DIFY_WORKFLOW_ID: str | None = None
    DIFY_RESPONSE_MODE: Literal["blocking", "streaming"] = "blocking"
    DIFY_TEXT_INPUT_VARIABLE: str | None = None
    DIFY_FILE_INPUT_VARIABLE: str | None = None
    DIFY_ENABLE_TRACE: bool = False
    DIFY_USER_PREFIX: str = "guest"
    DIFY_DEBUG_LOG_PATH: str = "./data/dify_debug.jsonl"
    GRAPH_EXTRACTION_PROMPT: str | None = None
    GRAPH_EXTRACTION_MODEL_PROVIDER: str = "openai-compatible"
    GRAPH_EXTRACTION_MODEL_NAME: str | None = None
    GRAPH_EXTRACTION_MODEL_API_BASE_URL: str | None = None
    GRAPH_EXTRACTION_MODEL_API_KEY: str | None = None
    GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME: str | None = None
    GRAPH_EXTRACTION_MODEL_ENABLED: bool = False
    GRAPH_EXTRACTION_MODEL_THINKING_ENABLED: bool = True
    DOCUMENT_LOCAL_STORAGE_DIR: str = "./data/uploads"
    DOCUMENT_MAX_FILE_SIZE_BYTES: int = Field(default=15 * 1024 * 1024, gt=0)
    DOCUMENT_ALLOWED_EXTENSIONS: str | None = None
    DOCUMENT_ALLOWED_MIME_TYPES: str | None = None

    API_V1_PREFIX: str = ""
    HOST: str = "0.0.0.0"
    INITIAL_ADMIN_USERNAME: str | None = None
    PAGE_DEFAULTS: dict[str, Any] = Field(default_factory=dict)
    FEATURE_FLAGS: dict[str, Any] = Field(default_factory=dict)
    EXPORT_RULES: dict[str, Any] = Field(default_factory=dict)
    FIXED_MAPPINGS: dict[str, Any] = Field(default_factory=dict)
    RESERVED_INTEGRATIONS: dict[str, Any] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        class ConfigFileSettingsSource(PydanticBaseSettingsSource):
            def __call__(self) -> dict[str, Any]:
                init_values = init_settings()
                env_values = env_settings()
                dotenv_values = dotenv_settings()
                config_path = (
                    init_values.get("APP_CONFIG_PATH")
                    or env_values.get("APP_CONFIG_PATH")
                    or dotenv_values.get("APP_CONFIG_PATH")
                    or os.getenv("APP_CONFIG_PATH")
                )
                file_payload = _load_config_file(config_path)

                app_payload = file_payload.get("app", {})
                admin_payload = file_payload.get("admin", {})
                defaults_payload = file_payload.get("defaults", {})
                export_payload = file_payload.get("export", {})
                graph_payload = file_payload.get("graph", {})
                integrations_payload = file_payload.get("integrations", {})

                normalized_payload = {
                    "APP_NAME": app_payload.get("name"),
                    "APP_VERSION": app_payload.get("version"),
                    "APP_ENV": app_payload.get("env"),
                    "HOST": app_payload.get("host"),
                    "PORT": app_payload.get("port"),
                    "LOG_LEVEL": app_payload.get("log_level"),
                    "API_V1_PREFIX": app_payload.get("api_v1_prefix"),
                    "INITIAL_ADMIN_USERNAME": admin_payload.get("initial_username"),
                    "PAGE_DEFAULTS": defaults_payload.get("page", {}),
                    "FEATURE_FLAGS": defaults_payload.get("features", {}),
                    "EXPORT_RULES": export_payload.get("rules", {}),
                    "FIXED_MAPPINGS": defaults_payload.get("mappings", {}),
                    "RESERVED_INTEGRATIONS": integrations_payload,
                    "GRAPH_ENABLED": defaults_payload.get("features", {}).get("enable_graph_api"),
                    "GRAPH_RELOAD_ON_START": defaults_payload.get("features", {}).get("graph_reload_on_start"),
                    "GRAPH_DEFAULT_LIMIT": graph_payload.get("default_limit"),
                    "GRAPH_MAX_NEIGHBORS": graph_payload.get("max_neighbors"),
                    "GRAPH_EXPORT_DIR": graph_payload.get("export_dir"),
                    "GRAPH_IMPORT_DIR": graph_payload.get("import_dir"),
                    "GRAPH_SNAPSHOT_PATH": graph_payload.get("snapshot_path"),
                    "GRAPH_INSTANCE_LOCAL_PATH": graph_payload.get("instance_local_path"),
                    "GRAPH_INSTANCE_ID": graph_payload.get("instance_id"),
                    "GRAPH_DB_VERSION": graph_payload.get("db_version"),
                    "DIFY_BASE_URL": integrations_payload.get("dify", {}).get("base_url"),
                    "DIFY_TIMEOUT_SECONDS": integrations_payload.get("dify", {}).get("timeout_seconds"),
                    "DIFY_WORKFLOW_ID": integrations_payload.get("dify", {}).get("workflow_id"),
                    "DIFY_RESPONSE_MODE": integrations_payload.get("dify", {}).get("response_mode"),
                    "DIFY_TEXT_INPUT_VARIABLE": integrations_payload.get("dify", {}).get("text_input_variable"),
                    "DIFY_FILE_INPUT_VARIABLE": integrations_payload.get("dify", {}).get("file_input_variable"),
                    "DIFY_ENABLE_TRACE": integrations_payload.get("dify", {}).get("enable_trace"),
                    "DIFY_USER_PREFIX": integrations_payload.get("dify", {}).get("user_prefix"),
                }
                return {key: value for key, value in normalized_payload.items() if value is not None}

            def get_field_value(self, field, field_name: str) -> tuple[Any, str, bool]:
                raise NotImplementedError

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            ConfigFileSettingsSource(settings_cls),
            file_secret_settings,
        )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_debug(self) -> bool:
        return self.APP_ENV in {"development", "test"}

    @property
    def sqlite_url(self) -> str:
        sqlite_path = Path(self.SQLITE_PATH).expanduser()
        return f"sqlite:///{sqlite_path}"

    @property
    def graph_instance_path(self) -> Path:
        if self.GRAPH_INSTANCE_LOCAL_PATH:
            return Path(self.GRAPH_INSTANCE_LOCAL_PATH).expanduser()

        base_path = Path(self.SQLITE_PATH).expanduser()
        return base_path.with_name("atlascore_graph.db")

    @property
    def graph_snapshot_path(self) -> Path:
        if self.GRAPH_SNAPSHOT_PATH:
            return Path(self.GRAPH_SNAPSHOT_PATH).expanduser()
        return self.graph_instance_path

    @property
    def graph_sqlite_url(self) -> str:
        return f"sqlite:///{self.graph_instance_path}"

    @property
    def runtime_paths(self) -> dict[str, Path]:
        return {
            "sqlite_path": Path(self.SQLITE_PATH).expanduser(),
            "csv_export_dir": Path(self.CSV_EXPORT_DIR).expanduser(),
            "document_storage_dir": Path(self.DOCUMENT_LOCAL_STORAGE_DIR).expanduser(),
            "graph_export_dir": Path(self.GRAPH_EXPORT_DIR).expanduser(),
            "graph_import_dir": Path(self.GRAPH_IMPORT_DIR).expanduser(),
            "graph_snapshot_path": self.graph_snapshot_path,
            "graph_instance_local_path": self.graph_instance_path,
        }

    @staticmethod
    def _parse_csv_values(value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip().lower() for item in value.split(",") if item.strip()]

    @property
    def document_allowed_extensions(self) -> list[str]:
        return self._parse_csv_values(self.DOCUMENT_ALLOWED_EXTENSIONS)

    @property
    def document_allowed_mime_types(self) -> list[str]:
        return self._parse_csv_values(self.DOCUMENT_ALLOWED_MIME_TYPES)

    def _secret_resolver(self) -> SecretResolver:
        return SecretResolver(self)

    def resolve_secret(
        self,
        *,
        env_var: str,
        secret_name_var: str | None = None,
        required: bool = False,
        allow_missing_in_dev: bool = True,
    ) -> ResolvedSecret:
        return self._secret_resolver().resolve(
            env_var=env_var,
            secret_name_var=secret_name_var,
            required=required,
            allow_missing_in_dev=allow_missing_in_dev,
        )

    @property
    def resolved_jwt_secret(self) -> str | None:
        return self.resolve_secret(
            env_var="JWT_SECRET",
            secret_name_var="JWT_SECRET_NAME",
            required=self.is_production,
            allow_missing_in_dev=False,
        ).value

    @property
    def resolved_initial_admin_password(self) -> str | None:
        return self.resolve_secret(
            env_var="INITIAL_ADMIN_PASSWORD",
            secret_name_var="INITIAL_ADMIN_PASSWORD_SECRET_NAME",
        ).value

    @property
    def resolved_admin_auth_secret(self) -> str | None:
        return self.resolve_secret(
            env_var="ADMIN_AUTH_SECRET",
            secret_name_var="ADMIN_AUTH_SECRET_NAME",
        ).value

    @property
    def resolved_admin_password_hash(self) -> str | None:
        return self.resolve_secret(
            env_var="ADMIN_PASSWORD_HASH",
            secret_name_var="ADMIN_PASSWORD_HASH_SECRET_NAME",
        ).value

    @property
    def resolved_dify_api_key(self) -> str | None:
        return self.resolve_secret(
            env_var="DIFY_API_KEY",
            secret_name_var="DIFY_API_KEY_SECRET_NAME",
        ).value

    @property
    def resolved_graph_extraction_model_api_key(self) -> str | None:
        return self.resolve_secret(
            env_var="GRAPH_EXTRACTION_MODEL_API_KEY",
            secret_name_var="GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME",
        ).value

    @property
    def dify_settings(self):
        from app.integrations.dify.schemas import DifySettings

        return DifySettings(
            base_url=self.DIFY_BASE_URL,
            api_key=self.resolved_dify_api_key,
            timeout_seconds=self.DIFY_TIMEOUT_SECONDS,
            workflow_id=self.DIFY_WORKFLOW_ID,
            response_mode=self.DIFY_RESPONSE_MODE,
            text_input_variable=self.DIFY_TEXT_INPUT_VARIABLE,
            file_input_variable=self.DIFY_FILE_INPUT_VARIABLE,
            enable_trace=self.DIFY_ENABLE_TRACE,
            user_prefix=self.DIFY_USER_PREFIX,
        )

    def secret_status_summary(self) -> dict[str, dict[str, str | bool]]:
        tracked = {
            "JWT_SECRET": ("JWT_SECRET", "JWT_SECRET_NAME"),
            "INITIAL_ADMIN_PASSWORD": ("INITIAL_ADMIN_PASSWORD", "INITIAL_ADMIN_PASSWORD_SECRET_NAME"),
            "ADMIN_AUTH_SECRET": ("ADMIN_AUTH_SECRET", "ADMIN_AUTH_SECRET_NAME"),
            "ADMIN_PASSWORD_HASH": ("ADMIN_PASSWORD_HASH", "ADMIN_PASSWORD_HASH_SECRET_NAME"),
            "DIFY_API_KEY": ("DIFY_API_KEY", "DIFY_API_KEY_SECRET_NAME"),
            "GRAPH_EXTRACTION_MODEL_API_KEY": (
                "GRAPH_EXTRACTION_MODEL_API_KEY",
                "GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME",
            ),
        }
        summary: dict[str, dict[str, str | bool]] = {}
        for label, (env_var, secret_name_var) in tracked.items():
            try:
                resolved = self.resolve_secret(
                    env_var=env_var,
                    secret_name_var=secret_name_var,
                    required=False,
                )
            except SecretResolutionError as exc:
                summary[label] = {"configured": False, "source": "error", "detail": str(exc)}
                continue
            summary[label] = {"configured": resolved.is_configured, "source": resolved.source}
        return summary

    def is_dify_configured(self) -> bool:
        try:
            return bool(self.DIFY_BASE_URL and self.resolved_dify_api_key)
        except SecretResolutionError:
            return False

    def is_admin_auth_configured(self) -> bool:
        jwt_configured = bool(self.resolved_jwt_secret)
        admin_seed_configured = bool(self.INITIAL_ADMIN_USERNAME and self.resolved_initial_admin_password)
        admin_hash_configured = bool(self.resolved_admin_password_hash)
        admin_secret_configured = bool(self.resolved_admin_auth_secret)
        return jwt_configured and (admin_seed_configured or admin_hash_configured or admin_secret_configured)

    def ensure_runtime_directories(self) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        results["sqlite_path"] = self._inspect_path(
            self.runtime_paths["sqlite_path"],
            path_kind="file",
            create_parent=True,
            check_read=False,
            check_write=True,
        )
        results["csv_export_dir"] = self._inspect_path(
            self.runtime_paths["csv_export_dir"],
            path_kind="dir",
            create_parent=True,
            check_read=True,
            check_write=True,
        )
        results["document_storage_dir"] = self._inspect_path(
            self.runtime_paths["document_storage_dir"],
            path_kind="dir",
            create_parent=True,
            check_read=True,
            check_write=True,
        )
        results["graph_export_dir"] = self._inspect_path(
            self.runtime_paths["graph_export_dir"],
            path_kind="dir",
            create_parent=True,
            check_read=True,
            check_write=True,
        )
        results["graph_import_dir"] = self._inspect_path(
            self.runtime_paths["graph_import_dir"],
            path_kind="dir",
            create_parent=True,
            check_read=True,
            check_write=True,
        )
        results["graph_instance_local_path"] = self._inspect_path(
            self.runtime_paths["graph_instance_local_path"],
            path_kind="file",
            create_parent=True,
            check_read=False,
            check_write=True,
        )
        results["graph_snapshot_path"] = self._inspect_path(
            self.runtime_paths["graph_snapshot_path"],
            path_kind="file",
            create_parent=True,
            check_read=False,
            check_write=True,
        )
        return results

    def runtime_config_summary(self) -> dict[str, Any]:
        path_summary = self.ensure_runtime_directories()
        return {
            "app_env": self.APP_ENV,
            "app_name": self.APP_NAME,
            "app_version": self.APP_VERSION,
            "port": self.PORT,
            "log_level": self.LOG_LEVEL,
            "app_config_path_configured": bool(self.APP_CONFIG_PATH),
            "graph_enabled": self.GRAPH_ENABLED,
            "graph_instance_id": self.GRAPH_INSTANCE_ID,
            "graph_db_version": self.GRAPH_DB_VERSION,
            "graph_extraction_model_enabled": self.GRAPH_EXTRACTION_MODEL_ENABLED,
            "graph_extraction_model_provider": self.GRAPH_EXTRACTION_MODEL_PROVIDER,
            "graph_extraction_model_name": self.GRAPH_EXTRACTION_MODEL_NAME,
            "graph_extraction_model_thinking_enabled": self.GRAPH_EXTRACTION_MODEL_THINKING_ENABLED,
            "dify_configured": self.is_dify_configured(),
            "admin_auth_configured": self.is_admin_auth_configured(),
            "paths": path_summary,
            "secrets": self.secret_status_summary(),
        }

    @staticmethod
    def _is_writable(path: Path, *, path_kind: Literal["dir", "file"]) -> bool:
        target = path if path_kind == "dir" else path.parent
        return os.access(target, os.W_OK)

    @staticmethod
    def _is_readable(path: Path, *, path_kind: Literal["dir", "file"]) -> bool:
        target = path if path_kind == "dir" else path.parent
        return os.access(target, os.R_OK)

    def _inspect_path(
        self,
        path: Path,
        *,
        path_kind: Literal["dir", "file"],
        create_parent: bool,
        check_read: bool,
        check_write: bool,
    ) -> dict[str, Any]:
        resolved = path.expanduser()
        parent = resolved if path_kind == "dir" else resolved.parent
        if create_parent:
            parent.mkdir(parents=True, exist_ok=True)
        exists = resolved.exists()
        if path_kind == "dir" and not exists:
            resolved.mkdir(parents=True, exist_ok=True)
            exists = True
        return {
            "path": str(resolved),
            "exists": exists,
            "parent_exists": parent.exists(),
            "readable": self._is_readable(resolved, path_kind=path_kind) if check_read else None,
            "writable": self._is_writable(resolved, path_kind=path_kind) if check_write else None,
        }

    @model_validator(mode="after")
    def validate_critical_config(self) -> "Settings":
        try:
            jwt_secret = self.resolve_secret(
                env_var="JWT_SECRET",
                secret_name_var="JWT_SECRET_NAME",
                required=self.is_production,
                allow_missing_in_dev=False,
            ).value
        except SecretResolutionError as exc:
            raise ValueError(str(exc)) from exc
        if self.is_production and not jwt_secret:
            raise ValueError("JWT_SECRET is required when APP_ENV=production")

        neo4j_values = [self.NEO4J_URI, self.NEO4J_USERNAME, self.NEO4J_PASSWORD]
        if any(neo4j_values) and not all(neo4j_values):
            raise ValueError(
                "NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be provided together"
            )

        try:
            dify_api_key = self.resolve_secret(
                env_var="DIFY_API_KEY",
                secret_name_var="DIFY_API_KEY_SECRET_NAME",
            ).value
        except SecretResolutionError as exc:
            raise ValueError(str(exc)) from exc

        dify_values = [self.DIFY_BASE_URL, dify_api_key]
        if any(dify_values) and not all(dify_values):
            raise ValueError("DIFY_BASE_URL and DIFY_API_KEY must be provided together")

        self.ensure_runtime_directories()

        return self


settings = Settings()
