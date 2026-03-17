from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.integrations.dify import DifyClient, DifyClientError, DifySettings
from app.schemas.admin import DifyDebugRequest

logger = get_logger(__name__)


class DifyDebugService:
    async def run_debug_check(self, payload: DifyDebugRequest) -> dict[str, Any]:
        dify_settings = DifySettings(
            base_url=payload.base_url,
            api_key=payload.api_key,
            timeout_seconds=payload.timeout_seconds,
            workflow_id=payload.workflow_id,
            response_mode=payload.response_mode,  # type: ignore[arg-type]
            text_input_variable=payload.text_input_variable,
            file_input_variable=payload.file_input_variable,
            enable_trace=payload.enable_trace,
            user_prefix=payload.user_prefix,
        )
        client = DifyClient(dify_settings=dify_settings)
        config_summary = {
            "base_url": payload.base_url.rstrip("/"),
            "workflow_id": payload.workflow_id,
            "response_mode": payload.response_mode,
            "text_input_variable": payload.text_input_variable,
            "file_input_variable": payload.file_input_variable,
            "enable_trace": payload.enable_trace,
            "user_prefix": payload.user_prefix,
            "api_key_configured": True,
        }

        workflow_result: dict[str, Any] | None = None
        info: dict[str, Any] | None = None
        parameters: dict[str, Any] | None = None
        warnings: list[str] = []
        reachable = False
        validation_ok = False
        status = "success"
        error_detail: str | None = None
        try:
            info = await client.get_info()
        except DifyClientError as exc:
            warnings.append(f"GET /info failed: {exc}")

        try:
            validation = await client.validate_configuration()
            reachable = validation.reachable
            validation_ok = validation.ok
            parameters = validation.raw_parameters
            warnings.extend(validation.warnings)
        except DifyClientError as exc:
            status = "failed"
            error_detail = str(exc)
            self._append_log(
                event="dify_debug_check",
                status=status,
                payload={
                    "config_summary": config_summary,
                    "reachable": reachable,
                    "validation_ok": validation_ok,
                    "warnings": warnings,
                    "error": error_detail,
                },
            )
            raise

        if payload.sample_text and payload.text_input_variable:
            try:
                result = await client.run_workflow(
                    inputs={payload.text_input_variable: payload.sample_text},
                    user=f"{payload.user_prefix}-manual-debug",
                    response_mode=payload.response_mode,
                    trace_id=f"dify-debug-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}" if payload.enable_trace else None,
                )
                workflow_result = {
                    "workflow_run_id": result.workflow_run_id,
                    "task_id": result.task_id,
                    "status": result.status,
                    "outputs": result.outputs,
                    "error": result.error,
                    "elapsed_time": result.elapsed_time,
                    "total_tokens": result.total_tokens,
                    "total_steps": result.total_steps,
                }
            except DifyClientError as exc:
                status = "partial_failure"
                error_detail = str(exc)
                warnings.append(f"Workflow run failed: {exc}")

        response_payload = {
            "reachable": reachable,
            "validation_ok": validation_ok,
            "config_summary": config_summary,
            "parameters": parameters,
            "info": info,
            "workflow_result": workflow_result,
            "warnings": warnings,
            "logs_saved_to": str(self._log_path()),
        }
        self._append_log(
            event="dify_debug_check",
            status=status,
            payload={
                "config_summary": config_summary,
                "reachable": reachable,
                "validation_ok": validation_ok,
                "warnings": warnings,
                "info_keys": sorted(info.keys()) if isinstance(info, dict) else [],
                "parameter_keys": sorted(parameters.keys()) if isinstance(parameters, dict) else [],
                "workflow_result": workflow_result,
                "error": error_detail,
                "sample_text_preview": (payload.sample_text or "")[:120] or None,
            },
        )
        return response_payload

    def list_recent_logs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        path = self._log_path()
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        items: list[dict[str, Any]] = []
        for line in reversed(lines[-limit:]):
            if not line.strip():
                continue
            items.append(json.loads(line))
        return items

    def _append_log(self, *, event: str, status: str, payload: dict[str, Any]) -> None:
        log_event(logger, 20, event, status, payload=payload)
        path = self._log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "event": event,
            "status": status,
            "payload": payload,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True, default=str) + "\n")

    @staticmethod
    def _log_path() -> Path:
        return Path(settings.DIFY_DEBUG_LOG_PATH).expanduser()


dify_debug_service = DifyDebugService()
