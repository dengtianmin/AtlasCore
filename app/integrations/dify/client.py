from __future__ import annotations

import json
import socket
from typing import Any, Protocol
from urllib import error, request
from uuid import uuid4

from app.core.config import settings
from app.integrations.dify.exceptions import (
    DifyConfigurationError,
    DifyRequestError,
    DifyTimeoutError,
)
from app.integrations.dify.schemas import (
    DifyChatRequest,
    DifyChatResponse,
    DifyDocumentIndexRequest,
    DifyJobResponse,
)


class DifyClientProtocol(Protocol):
    def is_enabled(self) -> bool:
        ...

    def check_reachable(self) -> bool:
        ...

    def chat(self, payload: DifyChatRequest) -> DifyChatResponse:
        ...

    def enqueue_document_index(self, payload: DifyDocumentIndexRequest) -> DifyJobResponse:
        ...


class DifyClient:
    def is_enabled(self) -> bool:
        return bool(settings.DIFY_BASE_URL and settings.resolved_dify_api_key)

    def check_reachable(self) -> bool:
        self._ensure_configured()
        base_url = self._base_url()
        req = request.Request(url=base_url, method="GET", headers=self._headers(include_content_type=False))
        try:
            with request.urlopen(req, timeout=self._timeout()) as response:
                return 200 <= response.status < 500
        except error.HTTPError as exc:
            return 200 <= exc.code < 500
        except (error.URLError, TimeoutError, socket.timeout):
            return False

    def chat(self, payload: DifyChatRequest) -> DifyChatResponse:
        self._ensure_configured()
        body = {
            "inputs": {},
            "query": payload.query,
            "response_mode": "blocking",
            "conversation_id": payload.session_id,
            "user": payload.user,
        }
        raw = self._request_json("chat-messages", body)
        answer = str(raw.get("answer") or "").strip()
        if not answer:
            raise DifyRequestError("Dify response did not contain an answer")

        retriever_resources = raw.get("metadata", {}).get("retriever_resources", [])
        sources: list[dict[str, str | None]] = []
        snippets: list[str] = []
        if isinstance(retriever_resources, list):
            for item in retriever_resources:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("document_name") or item.get("segment_id") or "dify-context")
                snippet = str(item.get("content") or "").strip() or None
                source = str(item.get("data_source_type") or item.get("dataset_name") or "dify")
                sources.append({"title": title, "snippet": snippet, "source": source})
                if snippet:
                    snippets.append(snippet)

        metadata = raw.get("metadata")
        safe_metadata: dict[str, str | int | float | bool | None] = {}
        if isinstance(metadata, dict):
            usage = metadata.get("usage")
            if isinstance(usage, dict):
                for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    value = usage.get(key)
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        safe_metadata[key] = value
            retriever_count = len(retriever_resources) if isinstance(retriever_resources, list) else 0
            safe_metadata["retriever_resource_count"] = retriever_count

        return DifyChatResponse(
            answer=answer,
            source="dify",
            sources=sources,
            retrieved_context="\n\n".join(snippets) or None,
            session_id=str(raw.get("conversation_id") or payload.session_id),
            provider_message_id=str(raw.get("message_id") or "") or None,
            metadata=safe_metadata,
        )

    def enqueue_document_index(self, payload: DifyDocumentIndexRequest) -> DifyJobResponse:
        if not self.is_enabled():
            return DifyJobResponse(
                job_id=f"placeholder-{payload.document_id}",
                status="queued",
                message="Dify integration is not configured; queued as placeholder only",
            )

        return DifyJobResponse(
            job_id=f"dify-{uuid4().hex}",
            status="queued",
            message="Dify integration configured; real API call not implemented in this stage",
        )

    def _request_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        base_url = self._base_url().rstrip("/")
        req = request.Request(
            url=f"{base_url}/v1/{endpoint.lstrip('/')}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=self._headers(include_content_type=True),
        )
        try:
            with request.urlopen(req, timeout=self._timeout()) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise DifyRequestError(f"Dify request failed with status {exc.code}: {detail or exc.reason}") from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, socket.timeout):
                raise DifyTimeoutError("Dify request timed out") from exc
            if isinstance(exc, TimeoutError):
                raise DifyTimeoutError("Dify request timed out") from exc
            raise DifyRequestError(f"Dify request failed: {reason}") from exc

        try:
            payload_obj = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise DifyRequestError("Dify returned invalid JSON") from exc
        if not isinstance(payload_obj, dict):
            raise DifyRequestError("Dify returned an unexpected response body")
        return payload_obj

    @staticmethod
    def _timeout() -> float:
        timeout = getattr(settings, "DIFY_TIMEOUT_SECONDS", 15.0)
        return float(timeout)

    def _ensure_configured(self) -> None:
        if not self.is_enabled():
            raise DifyConfigurationError("Dify is not configured")

    @staticmethod
    def _headers(*, include_content_type: bool) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {settings.resolved_dify_api_key}",
        }
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _base_url() -> str:
        return str(settings.DIFY_BASE_URL or "").rstrip("/")


def get_dify_client() -> DifyClientProtocol:
    return DifyClient()
