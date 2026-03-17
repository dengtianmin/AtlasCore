import asyncio
import json
from pathlib import Path

from app.api.v1.admin_system import debug_dify, list_dify_debug_logs
from app.auth.principal import Principal
from app.core.config import settings
from app.integrations.dify import DifyValidationResult
from app.schemas.admin import DifyDebugRequest


def _admin() -> Principal:
    return Principal(user_id="00000000-0000-0000-0000-000000000001", username="admin", roles=["admin"])


class StubDifyClient:
    def __init__(self, *, dify_settings, transport=None) -> None:
        self.settings = dify_settings

    async def get_info(self):
        return {"name": "debug-app", "mode": "workflow"}

    async def validate_configuration(self):
        return DifyValidationResult(
            ok=True,
            reachable=True,
            text_input_variable_exists=True,
            file_input_variable_exists=True,
            file_upload_enabled=True,
            warnings=[],
            raw_parameters={"user_input_form": [{"variable": "question"}]},
        )

    async def run_workflow(self, *, inputs, user, response_mode, trace_id=None):
        return type(
            "WorkflowResult",
            (),
            {
                "workflow_run_id": "run-debug-1",
                "task_id": "task-debug-1",
                "status": "succeeded",
                "outputs": {"text": f"echo:{next(iter(inputs.values()))}"},
                "error": None,
                "elapsed_time": 0.3,
                "total_tokens": 7,
                "total_steps": 1,
            },
        )()


def test_debug_dify_saves_log(monkeypatch, tmp_path):
    log_path = tmp_path / "dify-debug.jsonl"
    monkeypatch.setattr(settings, "DIFY_DEBUG_LOG_PATH", str(log_path))
    monkeypatch.setattr("app.services.dify_debug_service.DifyClient", StubDifyClient)

    payload = DifyDebugRequest(
        base_url="https://dify.example.com",
        api_key="secret-key",
        workflow_id="wf-1",
        text_input_variable="question",
        sample_text="hello atlas",
    )

    result = asyncio.run(debug_dify(payload, _=_admin()))

    assert result.reachable is True
    assert result.validation_ok is True
    assert result.workflow_result is not None
    assert result.workflow_result["workflow_run_id"] == "run-debug-1"
    assert log_path.exists()

    content = log_path.read_text(encoding="utf-8")
    assert "secret-key" not in content
    saved = json.loads(content.strip().splitlines()[-1])
    assert saved["payload"]["config_summary"]["base_url"] == "https://dify.example.com"
    assert saved["payload"]["workflow_result"]["task_id"] == "task-debug-1"


def test_list_dify_debug_logs_returns_recent_items(monkeypatch, tmp_path):
    log_path = tmp_path / "dify-debug.jsonl"
    monkeypatch.setattr(settings, "DIFY_DEBUG_LOG_PATH", str(log_path))
    entries = [
        {
            "recorded_at": "2026-03-17T10:00:00+00:00",
            "event": "dify_debug_check",
            "status": "success",
            "payload": {"base_url": "https://a.example.com"},
        },
        {
            "recorded_at": "2026-03-17T10:01:00+00:00",
            "event": "dify_debug_check",
            "status": "failed",
            "payload": {"base_url": "https://b.example.com"},
        },
    ]
    log_path.write_text("\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8")

    result = list_dify_debug_logs(_=_admin(), limit=20)

    assert len(result.items) == 2
    assert result.items[0].payload["base_url"] == "https://b.example.com"
    assert result.items[1].payload["base_url"] == "https://a.example.com"
