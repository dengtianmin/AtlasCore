from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlparse

if TYPE_CHECKING:
    from app.core.config import Settings


SecretSource = Literal["env", "kv_reference", "key_vault_sdk", "missing"]

_KEY_VAULT_REFERENCE_PATTERN = re.compile(r"^@Microsoft\.KeyVault\((?P<body>.+)\)$")


class SecretResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedSecret:
    value: str | None
    source: SecretSource

    @property
    def is_configured(self) -> bool:
        return bool(self.value)


@dataclass(frozen=True)
class ParsedKeyVaultReference:
    secret_name: str
    vault_url: str | None


def _parse_key_vault_reference(raw_value: str) -> ParsedKeyVaultReference | None:
    match = _KEY_VAULT_REFERENCE_PATTERN.match(raw_value.strip())
    if not match:
        return None

    body = match.group("body")
    parts = {}
    for item in body.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts[key.strip()] = value.strip()

    secret_uri = parts.get("SecretUri")
    if secret_uri:
        parsed = urlparse(secret_uri)
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0].lower() == "secrets":
            return ParsedKeyVaultReference(
                secret_name=path_parts[1],
                vault_url=f"{parsed.scheme}://{parsed.netloc}",
            )

    vault_name = parts.get("VaultName")
    secret_name = parts.get("SecretName")
    if vault_name and secret_name:
        return ParsedKeyVaultReference(
            secret_name=secret_name,
            vault_url=f"https://{vault_name}.vault.azure.net",
        )

    return None


class SecretResolver:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client_cache: dict[str, object] = {}

    def resolve(
        self,
        *,
        env_var: str,
        secret_name_var: str | None = None,
        required: bool = False,
        allow_missing_in_dev: bool = True,
    ) -> ResolvedSecret:
        raw_value = self._get_value(env_var)
        parsed_reference = _parse_key_vault_reference(raw_value) if raw_value else None
        if raw_value and parsed_reference is None:
            return ResolvedSecret(value=raw_value, source="env")

        if parsed_reference is not None:
            try:
                resolved = self._resolve_from_key_vault(
                    secret_name=parsed_reference.secret_name,
                    vault_url=parsed_reference.vault_url,
                    source="kv_reference",
                )
            except SecretResolutionError as exc:
                return self._handle_missing(
                    env_var=env_var,
                    secret_name_var=secret_name_var,
                    required=required,
                    allow_missing_in_dev=allow_missing_in_dev,
                    detail=str(exc),
                )
            if resolved.value:
                return resolved
            return self._handle_missing(
                env_var=env_var,
                secret_name_var=secret_name_var,
                required=required,
                allow_missing_in_dev=allow_missing_in_dev,
                detail=f"Key Vault reference for {env_var} could not be resolved",
            )

        secret_name = self._get_value(secret_name_var) if secret_name_var else None
        if secret_name:
            try:
                resolved = self._resolve_from_key_vault(
                    secret_name=secret_name,
                    vault_url=self._settings.KEY_VAULT_URL or self._settings.AZURE_KEY_VAULT_URL,
                    source="key_vault_sdk",
                )
            except SecretResolutionError as exc:
                return self._handle_missing(
                    env_var=env_var,
                    secret_name_var=secret_name_var,
                    required=required,
                    allow_missing_in_dev=allow_missing_in_dev,
                    detail=str(exc),
                )
            if resolved.value:
                return resolved
            return self._handle_missing(
                env_var=env_var,
                secret_name_var=secret_name_var,
                required=required,
                allow_missing_in_dev=allow_missing_in_dev,
                detail=f"Azure Key Vault secret '{secret_name}' for {env_var} could not be resolved",
            )

        return self._handle_missing(
            env_var=env_var,
            secret_name_var=secret_name_var,
            required=required,
            allow_missing_in_dev=allow_missing_in_dev,
        )

    def _handle_missing(
        self,
        *,
        env_var: str,
        secret_name_var: str | None,
        required: bool,
        allow_missing_in_dev: bool,
        detail: str | None = None,
    ) -> ResolvedSecret:
        if required and (not self._settings.is_debug or not allow_missing_in_dev):
            reference_hint = f" or {secret_name_var}" if secret_name_var else ""
            suffix = f": {detail}" if detail else ""
            raise SecretResolutionError(
                f"{env_var} is required but was not resolved from {env_var}{reference_hint}{suffix}"
            )
        return ResolvedSecret(value=None, source="missing")

    def _resolve_from_key_vault(
        self,
        *,
        secret_name: str,
        vault_url: str | None,
        source: SecretSource,
    ) -> ResolvedSecret:
        if not vault_url:
            raise SecretResolutionError(
                f"KEY_VAULT_URL or AZURE_KEY_VAULT_URL is required to resolve secret '{secret_name}'"
            )

        if not self._settings.KEY_VAULT_ENABLED and source != "kv_reference":
            return ResolvedSecret(value=None, source="missing")

        client = self._get_secret_client(vault_url)
        try:
            secret_bundle = client.get_secret(secret_name)
        except Exception as exc:  # pragma: no cover - exercised with mocks in tests
            raise SecretResolutionError(
                f"Failed to load secret '{secret_name}' from Azure Key Vault at {vault_url}"
            ) from exc

        value = getattr(secret_bundle, "value", None)
        if not value:
            raise SecretResolutionError(
                f"Azure Key Vault returned an empty value for secret '{secret_name}'"
            )
        return ResolvedSecret(value=value, source=source)

    def _get_secret_client(self, vault_url: str):
        if vault_url in self._client_cache:
            return self._client_cache[vault_url]

        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
        except ImportError as exc:
            raise SecretResolutionError(
                "Azure Key Vault SDK is not installed; add azure-identity and azure-keyvault-secrets"
            ) from exc

        client_kwargs: dict[str, object] = {}
        try:
            from azure.core.pipeline.transport import RequestsTransport

            client_kwargs["transport"] = RequestsTransport(
                connection_timeout=self._settings.KEY_VAULT_TIMEOUT_SECONDS,
                read_timeout=self._settings.KEY_VAULT_TIMEOUT_SECONDS,
            )
        except ImportError:
            pass

        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=True,
        )
        client = SecretClient(vault_url=vault_url, credential=credential, **client_kwargs)
        self._client_cache[vault_url] = client
        return client

    def _get_value(self, field_name: str | None) -> str | None:
        if not field_name:
            return None
        value = getattr(self._settings, field_name, None)
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value
