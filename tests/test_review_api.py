import asyncio

from fastapi import HTTPException

from app.api.v1.admin_review import get_review_dify_config, get_review_rubric, list_review_logs, update_review_dify_config, update_review_rubric
from app.api.v1.review import evaluate_review
from app.auth.principal import Principal
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import get_session_factory, reset_db_state
from app.schemas.review import ReviewDifyConfigUpdateRequest, ReviewEvaluationRequest, ReviewRubricUpdateRequest
from app.services.review_service import review_service


def _admin() -> Principal:
    return Principal(user_id="00000000-0000-0000-0000-000000000001", username="admin", roles=["admin"])


def _user() -> Principal:
    return Principal(
        user_id="11111111-1111-1111-1111-111111111111",
        username="2025000001",
        student_id="2025000001",
        name="张三",
        roles=["user"],
        role="user",
        scope="user",
        token_type="user_access",
    )


async def _run_lifespan() -> None:
    from fastapi import FastAPI

    async with lifespan(FastAPI()):
        pass


def _bootstrap_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "unit-test-secret")
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "runtime" / "atlascore.db"))
    monkeypatch.setattr(settings, "CSV_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setattr(settings, "DOCUMENT_LOCAL_STORAGE_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "GRAPH_EXPORT_DIR", str(tmp_path / "graph_exports"))
    monkeypatch.setattr(settings, "GRAPH_IMPORT_DIR", str(tmp_path / "graph_imports"))
    monkeypatch.setattr(settings, "GRAPH_INSTANCE_LOCAL_PATH", str(tmp_path / "graph" / "atlascore_graph.db"))
    monkeypatch.setattr(settings, "INITIAL_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "StrongPass123!")
    monkeypatch.setattr(settings, "REVIEW_DIFY_BASE_URL", "https://review-dify.example.com")
    monkeypatch.setattr(settings, "REVIEW_DIFY_API_KEY", "review-dify-secret")
    monkeypatch.setattr(settings, "REVIEW_DIFY_API_KEY_SECRET_NAME", None)
    monkeypatch.setattr(settings, "REVIEW_DIFY_APP_MODE", "workflow")
    monkeypatch.setattr(settings, "REVIEW_DIFY_RESPONSE_MODE", "blocking")
    monkeypatch.setattr(settings, "REVIEW_DIFY_TEXT_INPUT_VARIABLE", "answer_text")
    reset_db_state()
    asyncio.run(_run_lifespan())


def test_get_and_update_review_rubric(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    initial = get_review_rubric(_=_admin())
    assert initial.rubric_text == ""
    assert initial.is_active is False

    updated = update_review_rubric(
        ReviewRubricUpdateRequest(rubric_text="请围绕准确性、完整性和表达清晰度评分。"),
        current_admin=_admin(),
    )
    assert updated.rubric_text == "请围绕准确性、完整性和表达清晰度评分。"
    assert updated.updated_by == "admin"
    assert updated.is_active is True

    fetched = get_review_rubric(_=_admin())
    assert fetched.rubric_text == updated.rubric_text
    assert fetched.updated_at is not None


def test_get_and_update_review_dify_config(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    initial = get_review_dify_config(_=_admin())
    assert initial.enabled is True
    assert initial.app_mode == "workflow"
    assert initial.base_url == "https://review-dify.example.com"
    assert initial.has_api_key is True

    updated = update_review_dify_config(
        ReviewDifyConfigUpdateRequest(
            base_url="https://override-review-dify.example.com",
            api_key="override-secret",
            app_mode="chat",
            response_mode="blocking",
            timeout_seconds=45,
            workflow_id=None,
            text_input_variable="query",
            file_input_variable=None,
            enable_trace=True,
            user_prefix="review-user",
        ),
        current_admin=_admin(),
    )
    assert updated.app_mode == "chat"
    assert updated.timeout_seconds == 45
    assert updated.text_input_variable == "query"
    assert updated.base_url == "https://override-review-dify.example.com"
    assert updated.has_api_key is True


def test_evaluate_review_returns_controlled_error_without_rubric(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    with get_session_factory()() as db:
        try:
            asyncio.run(review_service.evaluate_answer(db, answer_text="这是一个待评阅答案", principal=_user()))
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "Review rubric is not configured. Please ask an administrator to set it first."
        else:
            raise AssertionError("Expected controlled error when rubric is missing")


def test_evaluate_review_returns_structured_result_and_writes_log(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    update_review_rubric(
        ReviewRubricUpdateRequest(rubric_text="重点考察论点准确、结构完整、表达清晰，满分 100 分。"),
        current_admin=_admin(),
    )

    async def fake_run_application(self, *, inputs, user, response_mode, trace_id=None):
        assert inputs["answer_text"] == "答案内容"
        assert "结构完整" in inputs["rubric_text"]
        assert user == "review:2025000001"
        assert response_mode == "blocking"
        return type(
            "WorkflowResult",
            (),
            {
                "workflow_run_id": "review-run-1",
                "task_id": "review-task-1",
                "status": "succeeded",
                "outputs": {
                    "text": """
```json
{"score": 86, "grade": "B+", "risk_level": "中风险", "summary": "整体较完整，但关键支撑不足。", "review_items": [{"item_name": "总平面", "conclusion": "需复核", "importance": "高", "scheme_excerpt": "道路组织描述较少", "standard_basis": "总平面组织应完整", "reason": "缺少疏散说明", "suggestion": "补充分流与疏散论证"}], "key_issues": [{"title": "总平面组织", "risk_level": "高风险", "problem": "流线说明不足", "basis": "评审标准第 2 条", "suggestion": "补充人车分流"}], "deduction_logic": [{"reason": "流线论证不完整", "deducted_score": 14}]}
```""",
                },
                "raw": {"data": {"outputs": {"text": "ignored"}}, "answer": "ignored"},
            },
        )()

    monkeypatch.setattr(DifyClientStubHolder, "run_application", fake_run_application)
    monkeypatch.setattr("app.services.review_service.DifyClient", DifyClientStubHolder)

    with get_session_factory()() as db:
        payload = asyncio.run(evaluate_review(ReviewEvaluationRequest(answer_text="答案内容"), principal=_user(), db=db))

    assert payload.score == 86
    assert payload.grade == "B+"
    assert payload.risk_level == "medium"
    assert payload.parse_status == "success"
    assert payload.review_log_id is not None

    logs = list_review_logs(_=_admin(), limit=50, offset=0)
    assert len(logs.items) == 1
    assert logs.items[0].student_id_snapshot == "2025000001"
    assert logs.items[0].score == 86


def test_evaluate_review_falls_back_to_raw_text_when_parse_failed(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    update_review_rubric(
        ReviewRubricUpdateRequest(rubric_text="按照准确性和完整性评分。"),
        current_admin=_admin(),
    )

    async def fake_run_application(self, *, inputs, user, response_mode, trace_id=None):
        return type(
            "WorkflowResult",
            (),
            {
                "workflow_run_id": "review-run-2",
                "task_id": "review-task-2",
                "status": "succeeded",
                "outputs": {"text": "本次方案缺少关键规范依据，建议补充总平面与进度证明材料。"},
                "raw": {"answer": "本次方案缺少关键规范依据，建议补充总平面与进度证明材料。"},
            },
        )()

    monkeypatch.setattr(DifyClientStubHolder, "run_application", fake_run_application)
    monkeypatch.setattr("app.services.review_service.DifyClient", DifyClientStubHolder)

    with get_session_factory()() as db:
        payload = asyncio.run(evaluate_review(ReviewEvaluationRequest(answer_text="答案内容"), principal=_user(), db=db))

    assert payload.score is None
    assert payload.parse_status == "failed"
    assert "关键规范依据" in (payload.raw_text or "")


def test_evaluate_review_rejects_blank_answer(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    update_review_rubric(
        ReviewRubricUpdateRequest(rubric_text="按照准确性和完整性评分。"),
        current_admin=_admin(),
    )

    with get_session_factory()() as db:
        try:
            asyncio.run(review_service.evaluate_answer(db, answer_text="   ", principal=_user()))
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "Answer text must not be empty"
        else:
            raise AssertionError("Expected controlled error for blank answer")


class DifyClientStubHolder:
    def __init__(self, *, dify_settings) -> None:
        self._settings = dify_settings

    async def run_application(self, *, inputs, user, response_mode, trace_id=None):
        raise NotImplementedError
