from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol
from uuid import uuid4

import httpx

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.integrations.dify.exceptions import (
    DifyAppUnavailableError,
    DifyAuthError,
    DifyBadRequestError,
    DifyClientError,
    DifyConfigurationError,
    DifyFileTooLargeError,
    DifyFileUploadError,
    DifyProviderInitError,
    DifyQuotaExceededError,
    DifyRequestError,
    DifyServiceUnavailableError,
    DifyTimeoutError,
    DifyUnsupportedFileTypeError,
    DifyWorkflowExecutionError,
    DifyWorkflowNotFoundError,
)
from app.integrations.dify.schemas import (
    DifyChatRequest,
    DifyChatResponse,
    DifyDocumentIndexRequest,
    DifyJobResponse,
    DifySettings,
    DifyUploadedFile,
    DifyValidationResult,
    DifyWorkflowResult,
)

logger = get_logger(__name__)


class DifyClientProtocol(Protocol):
    def is_enabled(self) -> bool:
        ...

    async def check_reachable(self) -> bool:
        ...

    async def validate_configuration(self) -> DifyValidationResult:
        ...

    async def run_workflow(
        self,
        inputs: dict[str, Any],
        user: str,
        response_mode: str = "blocking",
        trace_id: str | None = None,
    ) -> DifyWorkflowResult:
        ...

    async def upload_file(
        self,
        file_path: str,
        user: str,
        mime_type: str | None = None,
    ) -> DifyUploadedFile:
        ...


class DifyClient:
    def __init__(
        self,
        *,
        dify_settings: DifySettings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = dify_settings or settings.dify_settings
        self._transport = transport

    def is_enabled(self) -> bool:
        return self._settings.enabled

    async def check_reachable(self) -> bool:
        if not self.is_enabled():
            return False

        try:
            await self.get_parameters()
            return True
        except DifyConfigurationError:
            return False
        except DifyClientError:
            return False

    async def validate_configuration(self) -> DifyValidationResult:
        if not self.is_enabled():
            raise DifyConfigurationError("Dify is not configured")

        warnings: list[str] = []
        parameters = await self.get_parameters()
        input_names = self._extract_input_names(parameters)
        file_upload_enabled = self._detect_file_upload_enabled(parameters)

        text_var = self._settings.text_input_variable
        file_var = self._settings.file_input_variable

        text_ok = bool(text_var and text_var in input_names)
        file_ok = True
        if file_var:
            file_ok = file_var in input_names
            if not file_ok:
                warnings.append(f"Configured file input variable not found: {file_var}")
        if text_var and not text_ok:
            warnings.append(f"Configured text input variable not found: {text_var}")
        if file_var and not file_upload_enabled:
            warnings.append("Dify file upload is not enabled")
        if self._settings.workflow_id and "workflow_id" in parameters:
            if str(parameters.get("workflow_id")) != self._settings.workflow_id:
                warnings.append("Configured workflow_id does not match Dify parameters response")

        return DifyValidationResult(
            ok=bool(text_ok and file_ok and (file_upload_enabled or not file_var)),
            reachable=True,
            text_input_variable_exists=text_ok,
            file_input_variable_exists=file_ok,
            file_upload_enabled=file_upload_enabled,
            warnings=warnings,
            raw_parameters=parameters,
        )

    async def run_workflow(
        self,
        inputs: dict[str, Any],
        user: str,
        response_mode: str = "blocking",
        trace_id: str | None = None,
    ) -> DifyWorkflowResult:
        workflow_id = self._settings.workflow_id
        if workflow_id:
            return await self.run_workflow_by_id(
                workflow_id,
                inputs=inputs,
                user=user,
                response_mode=response_mode,
                trace_id=trace_id,
            )

        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user,
        }
        if trace_id and self._settings.enable_trace:
            payload["trace_id"] = trace_id
        raw = await self._request_json("POST", "/workflows/run", json_body=payload, user=user, trace_id=trace_id)
        return self._parse_workflow_result(raw)

    async def run_workflow_by_id(
        self,
        workflow_id: str,
        inputs: dict[str, Any],
        user: str,
        response_mode: str = "blocking",
        trace_id: str | None = None,
    ) -> DifyWorkflowResult:
        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user,
        }
        if trace_id and self._settings.enable_trace:
            payload["trace_id"] = trace_id
        raw = await self._request_json(
            "POST",
            f"/workflows/{workflow_id}/run",
            json_body=payload,
            user=user,
            trace_id=trace_id,
        )
        return self._parse_workflow_result(raw)

    async def upload_file(
        self,
        file_path: str,
        user: str,
        mime_type: str | None = None,
    ) -> DifyUploadedFile:
        path = Path(file_path).expanduser()
        if not path.exists():
            raise DifyFileUploadError("File does not exist", details={"file_path": str(path)})

        filename = path.name
        content_type = mime_type or "application/octet-stream"
        with path.open("rb") as file_handle:
            raw = await self._request_multipart(
                "POST",
                "/files/upload",
                data={"user": user},
                files={"file": (filename, file_handle, content_type)},
                user=user,
            )
        return DifyUploadedFile(
            file_id=str(raw.get("id") or raw.get("file_id") or ""),
            name=raw.get("name"),
            size=raw.get("size"),
            extension=raw.get("extension"),
            mime_type=raw.get("mime_type") or raw.get("content_type"),
            created_at=raw.get("created_at"),
            raw=raw,
        )

    async def get_parameters(self) -> dict[str, Any]:
        return await self._request_json("GET", "/parameters")

    async def get_workflow_run(self, workflow_run_id: str) -> dict[str, Any]:
        return await self._request_json("GET", f"/workflows/run/{workflow_run_id}")

    async def get_info(self) -> dict[str, Any]:
        return await self._request_json("GET", "/info")

    async def get_logs(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request_json("GET", "/workflows/logs", params=filters or {})

    async def stop_task(self, task_id: str, user: str) -> dict[str, Any]:
        return await self._request_json("POST", f"/workflows/tasks/{task_id}/stop", json_body={"user": user}, user=user)

    async def chat(self, payload: DifyChatRequest) -> DifyChatResponse:
        text_input_variable = self._settings.text_input_variable
        if not text_input_variable:
            raise DifyConfigurationError("DIFY_TEXT_INPUT_VARIABLE is not configured")

        result = await self.run_workflow(
            inputs={text_input_variable: payload.query},
            user=payload.user,
            response_mode=self._settings.response_mode,
            trace_id=payload.trace_id,
        )
        outputs = result.outputs
        answer = self._extract_answer(outputs)
        if not answer:
            raise DifyWorkflowExecutionError(
                "Dify workflow response did not contain a text output",
                details={"available_outputs": list(outputs.keys())},
                raw=result.raw,
            )
        return DifyChatResponse(
            answer=answer,
            source="dify",
            sources=[],
            retrieved_context=None,
            session_id=payload.session_id,
            provider_message_id=result.task_id or result.workflow_run_id,
            metadata={
                "workflow_run_id": result.workflow_run_id,
                "task_id": result.task_id,
                "status": result.status,
                "total_tokens": result.total_tokens,
                "total_steps": result.total_steps,
                "elapsed_time": result.elapsed_time,
            },
        )

    async def enqueue_document_index(self, payload: DifyDocumentIndexRequest) -> DifyJobResponse:
        uploaded = await self.upload_file(payload.source_uri or "", user=payload.document_id)
        return DifyJobResponse(
            job_id=uploaded.file_id,
            status="uploaded",
            message=f"Dify file uploaded: {uploaded.name or payload.title}",
        )

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        user: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            method,
            path,
            json_body=json_body,
            params=params,
            user=user,
            trace_id=trace_id,
        )

    async def _request_multipart(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any],
        files: dict[str, Any],
        user: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            method,
            path,
            data=data,
            files=files,
            user=user,
            trace_id=trace_id,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        user: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_configured()
        retries = 1 if method.upper() in {"POST"} else 2
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            started = perf_counter()
            try:
                async with self._build_http_client() as client:
                    response = await client.request(
                        method=method,
                        url=self._join_url(path),
                        headers=self._build_headers(),
                        json=json_body,
                        params=params,
                        data=data,
                        files=files,
                    )
                elapsed_ms = round((perf_counter() - started) * 1000, 2)
                payload = self._decode_json(response)
                if response.is_error:
                    self._log_request(
                        method=method,
                        path=path,
                        trace_id=trace_id,
                        user=user,
                        status_code=response.status_code,
                        elapsed_ms=elapsed_ms,
                        error_code=str(payload.get("code") or payload.get("error_code") or ""),
                        error_message=str(payload.get("message") or payload.get("error") or response.reason_phrase),
                    )
                    self._raise_for_dify_error(response.status_code, payload)
                self._log_request(
                    method=method,
                    path=path,
                    trace_id=trace_id,
                    user=user,
                    status_code=response.status_code,
                    elapsed_ms=elapsed_ms,
                    workflow_run_id=str(payload.get("workflow_run_id") or payload.get("id") or ""),
                    task_id=str(payload.get("task_id") or ""),
                )
                return payload
            except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
                last_error = DifyTimeoutError("Dify request timed out", details={"path": path})
            except httpx.HTTPError as exc:
                last_error = DifyServiceUnavailableError(
                    "Dify request failed due to a network error",
                    details={"path": path, "reason": str(exc)},
                )
            except DifyClientError as exc:
                last_error = exc
            if isinstance(last_error, DifyClientError) and not self._should_retry(last_error, attempt, retries):
                raise last_error
            await asyncio.sleep(0.2 * (2**attempt))
        assert last_error is not None
        raise last_error

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Accept": "application/json",
        }

    def _build_http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self._settings.timeout_seconds, transport=self._transport)

    def _join_url(self, path: str) -> str:
        return f"{str(self._settings.base_url or '').rstrip('/')}/v1/{path.lstrip('/')}"

    @property
    def active_settings(self) -> DifySettings:
        return self._settings

    def _parse_workflow_result(self, payload: dict[str, Any]) -> DifyWorkflowResult:
        workflow_run_id = payload.get("workflow_run_id")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        result = DifyWorkflowResult(
            workflow_run_id=str(workflow_run_id or data.get("id") or ""),
            task_id=str(payload.get("task_id") or data.get("task_id") or ""),
            status=data.get("status") or payload.get("status"),
            outputs=data.get("outputs") or {},
            error=data.get("error"),
            elapsed_time=data.get("elapsed_time"),
            total_tokens=data.get("total_tokens"),
            total_steps=data.get("total_steps"),
            raw=payload,
        )
        if result.status and result.status not in {"succeeded", "success", "completed"}:
            raise DifyWorkflowExecutionError(
                "Dify workflow execution failed",
                error_code=str(data.get("error_code") or ""),
                details={"status": result.status},
                raw=payload,
            )
        return result

    @staticmethod
    def _decode_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise DifyRequestError("Dify returned invalid JSON", status_code=response.status_code) from exc
        if not isinstance(payload, dict):
            raise DifyRequestError("Dify returned an unexpected response body", status_code=response.status_code)
        return payload

    @staticmethod
    def _extract_input_names(parameters: dict[str, Any]) -> set[str]:
        names: set[str] = set()
        fields = parameters.get("user_input_form") or parameters.get("inputs") or parameters.get("input_form")
        if isinstance(fields, list):
            for item in fields:
                if not isinstance(item, dict):
                    continue
                for key in ("variable", "name", "field", "input_variable"):
                    value = item.get(key)
                    if isinstance(value, str) and value:
                        names.add(value)
        elif isinstance(fields, dict):
            names.update(str(key) for key in fields.keys())
        return names

    @staticmethod
    def _detect_file_upload_enabled(parameters: dict[str, Any]) -> bool:
        features = parameters.get("features") or {}
        if isinstance(features, dict):
            file_upload = features.get("file_upload")
            if isinstance(file_upload, dict):
                return bool(file_upload.get("enabled"))
            if isinstance(file_upload, bool):
                return file_upload
        files = parameters.get("files") or parameters.get("file_upload")
        return bool(files)

    @staticmethod
    def _extract_answer(outputs: dict[str, Any]) -> str | None:
        preferred_keys = ("text", "answer", "output", "result")
        for key in preferred_keys:
            value = outputs.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in outputs.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _normalize_error_payload(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "code": payload.get("code") or payload.get("error_code"),
            "message": payload.get("message") or payload.get("error") or "Dify request failed",
            "status": payload.get("status"),
            "raw": payload,
        }

    def _raise_for_dify_error(self, status_code: int, payload: dict[str, Any]) -> None:
        normalized = self._normalize_error_payload(payload)
        error_code = str(normalized["code"] or "")
        message = str(normalized["message"])
        kwargs = {
            "status_code": status_code,
            "error_code": error_code or None,
            "raw": normalized["raw"],
        }
        if status_code in {401, 403}:
            raise DifyAuthError(message, **kwargs)
        if status_code == 404:
            raise DifyWorkflowNotFoundError(message, **kwargs)
        if status_code == 429:
            raise DifyQuotaExceededError(message, **kwargs)
        if status_code in {502, 503, 504}:
            raise DifyServiceUnavailableError(message, **kwargs)
        if error_code == "file_too_large":
            raise DifyFileTooLargeError(message, **kwargs)
        if error_code == "unsupported_file_type":
            raise DifyUnsupportedFileTypeError(message, **kwargs)
        if error_code in {"provider_not_initialize", "provider_initialization_failed"}:
            raise DifyProviderInitError(message, **kwargs)
        if error_code in {"app_unavailable", "workflow_app_unavailable"}:
            raise DifyAppUnavailableError(message, **kwargs)
        if status_code in {400, 422} or error_code == "invalid_param":
            raise DifyBadRequestError(message, **kwargs)
        raise DifyRequestError(message, **kwargs)

    @staticmethod
    def _should_retry(exc: DifyClientError, attempt: int, retries: int) -> bool:
        if attempt >= retries:
            return False
        return isinstance(exc, (DifyTimeoutError, DifyServiceUnavailableError))

    def _ensure_configured(self) -> None:
        if not self.is_enabled():
            raise DifyConfigurationError("Dify is not configured")

    def _log_request(
        self,
        *,
        method: str,
        path: str,
        trace_id: str | None,
        user: str | None,
        status_code: int,
        elapsed_ms: float,
        workflow_run_id: str | None = None,
        task_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        log_event(
            logger,
            logging.INFO if not error_code else logging.WARNING,
            "dify_client_request",
            "failed" if error_code else "success",
            method=method,
            path=path,
            trace_id=trace_id,
            user=user,
            workflow_run_id=workflow_run_id,
            task_id=task_id,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
            error_code=error_code,
            error_message=error_message,
        )


def get_dify_client() -> DifyClientProtocol:
    return DifyClient()
