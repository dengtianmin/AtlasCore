import asyncio

from fastapi import HTTPException

from app.api.v1.admin_review import get_review_rubric, update_review_rubric
from app.api.v1.review import evaluate_review
from app.auth.principal import Principal
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import get_session_factory, reset_db_state
from app.schemas.review import ReviewEvaluationRequest, ReviewRubricUpdateRequest
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
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_ENABLED", True)
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_PROVIDER", "openai-compatible")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_NAME", "review-model")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_BASE_URL", "http://review-model.local/v1")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_KEY", "review-secret")
    monkeypatch.setattr(settings, "GRAPH_EXTRACTION_MODEL_API_KEY_SECRET_NAME", None)
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


def test_evaluate_review_returns_controlled_error_without_rubric(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    with get_session_factory()() as db:
        try:
            asyncio.run(review_service.evaluate_answer(db, answer_text="这是一个待评阅答案"))
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "Review rubric is not configured. Please ask an administrator to set it first."
        else:
            raise AssertionError("Expected controlled error when rubric is missing")


def test_evaluate_review_returns_score_and_reason(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    update_review_rubric(
        ReviewRubricUpdateRequest(rubric_text="重点考察论点准确、结构完整、表达清晰，满分 100 分。"),
        current_admin=_admin(),
    )

    async def fake_call_model(*, answer_text, rubric_text, model_setting):
        assert answer_text == "答案内容"
        assert "结构完整" in rubric_text
        assert model_setting.model_name == "review-model"
        return '{"score": 86, "reason": "内容较完整，论点基本准确，但论证细节仍可加强。"}'

    monkeypatch.setattr(review_service, "_call_model", fake_call_model)

    with get_session_factory()() as db:
        payload = asyncio.run(evaluate_review(ReviewEvaluationRequest(answer_text="答案内容"), _=_user(), db=db))

    assert payload.score == 86
    assert "论点基本准确" in payload.reason
    assert payload.rubric_updated_at is not None


def test_evaluate_review_rejects_blank_answer(monkeypatch, tmp_path):
    _bootstrap_runtime(monkeypatch, tmp_path)

    update_review_rubric(
        ReviewRubricUpdateRequest(rubric_text="按照准确性和完整性评分。"),
        current_admin=_admin(),
    )

    with get_session_factory()() as db:
        try:
            asyncio.run(review_service.evaluate_answer(db, answer_text="   "))
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "Answer text must not be empty"
        else:
            raise AssertionError("Expected controlled error for blank answer")
