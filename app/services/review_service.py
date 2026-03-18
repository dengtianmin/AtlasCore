from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
import json
import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.principal import Principal
from app.core.config import settings
from app.integrations.dify import (
    DifyAuthError,
    DifyBadRequestError,
    DifyClient,
    DifyConfigurationError,
    DifyServiceUnavailableError,
    DifyTimeoutError,
    DifyWorkflowExecutionError,
)
from app.integrations.dify.schemas import DifySettings, DifyWorkflowResult
from app.models.review_dify_setting import ReviewDifySetting
from app.models.review_rubric_setting import ReviewRubricSetting
from app.repositories.review_dify_setting_repo import ReviewDifySettingRepository
from app.repositories.review_repo import ReviewRubricSettingRepository
from app.schemas.review import ReviewResultData
from app.services.review_log_service import review_log_service

DEFAULT_REVIEW_SUMMARY = "本次评阅未生成完整结构化结果，已返回可降级展示内容。"


class ReviewService:
    def __init__(self) -> None:
        self.rubric_repo = ReviewRubricSettingRepository()
        self.review_dify_repo = ReviewDifySettingRepository()

    def get_rubric(self, db: Session) -> dict:
        setting = self.rubric_repo.get_active(db)
        if setting is None:
            return {
                "rubric_text": "",
                "updated_at": None,
                "updated_by": None,
                "is_active": False,
            }
        return self._serialize_rubric(setting)

    def update_rubric(self, db: Session, *, rubric_text: str, operator: str) -> dict:
        normalized_rubric = rubric_text.strip()
        setting = ReviewRubricSetting(rubric_text=normalized_rubric, updated_by=operator, is_active=True)
        self.rubric_repo.replace_active(db, setting=setting)
        db.commit()
        return self._serialize_rubric(setting)

    def get_review_dify_config(self, db: Session) -> dict:
        resolved = self._resolve_review_dify_settings(db)
        return {
            "enabled": resolved.enabled,
            "app_mode": resolved.app_mode,
            "response_mode": resolved.response_mode,
            "timeout_seconds": resolved.timeout_seconds,
            "workflow_id_configured": bool(resolved.workflow_id),
            "text_input_variable": resolved.text_input_variable,
            "file_input_variable": resolved.file_input_variable,
            "enable_trace": resolved.enable_trace,
            "user_prefix": resolved.user_prefix,
        }

    def update_review_dify_config(self, db: Session, *, payload: dict, operator: str) -> dict:
        setting = ReviewDifySetting(
            app_mode=payload["app_mode"],
            response_mode=payload["response_mode"],
            timeout_seconds=payload["timeout_seconds"],
            workflow_id=payload.get("workflow_id"),
            text_input_variable=payload.get("text_input_variable"),
            file_input_variable=payload.get("file_input_variable"),
            enable_trace=payload["enable_trace"],
            user_prefix=payload["user_prefix"],
            updated_by=operator,
            is_active=True,
        )
        self.review_dify_repo.replace_active(db, setting=setting)
        db.commit()
        return self.get_review_dify_config(db)

    async def evaluate_answer(self, db: Session, *, answer_text: str, principal: Principal) -> dict:
        normalized_answer = answer_text.strip()
        if not normalized_answer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Answer text must not be empty")

        rubric = self.rubric_repo.get_active(db)
        if rubric is None or not rubric.rubric_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review rubric is not configured. Please ask an administrator to set it first.",
            )

        dify_settings = self._resolve_review_dify_settings(db)
        client = DifyClient(dify_settings=dify_settings)
        inputs = self._build_review_inputs(
            answer_text=normalized_answer,
            rubric_text=rubric.rubric_text,
            dify_settings=dify_settings,
        )
        user = self._build_dify_user(principal, dify_settings)

        try:
            result = await client.run_application(
                inputs=inputs,
                user=user,
                response_mode=dify_settings.response_mode,
                trace_id=principal.user_id if dify_settings.enable_trace else None,
            )
        except DifyConfigurationError as exc:
            self._log_provider_failure(
                db,
                principal=principal,
                review_input=normalized_answer,
                detail="Review Dify is not configured",
                error_code="review_dify_not_configured",
                dify_settings=dify_settings,
            )
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Review integration is not configured") from exc
        except DifyTimeoutError as exc:
            self._log_provider_failure(
                db,
                principal=principal,
                review_input=normalized_answer,
                detail="Review Dify request timed out",
                error_code="review_dify_timeout",
                dify_settings=dify_settings,
            )
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Review provider timed out") from exc
        except DifyBadRequestError as exc:
            self._log_provider_failure(
                db,
                principal=principal,
                review_input=normalized_answer,
                detail=str(exc),
                error_code="review_dify_bad_request",
                dify_settings=dify_settings,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review provider rejected request") from exc
        except DifyAuthError as exc:
            self._log_provider_failure(
                db,
                principal=principal,
                review_input=normalized_answer,
                detail=str(exc),
                error_code="review_dify_auth_failed",
                dify_settings=dify_settings,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review provider authentication failed") from exc
        except (DifyServiceUnavailableError, DifyWorkflowExecutionError) as exc:
            self._log_provider_failure(
                db,
                principal=principal,
                review_input=normalized_answer,
                detail=str(exc),
                error_code="review_dify_request_failed",
                dify_settings=dify_settings,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review provider request failed") from exc

        normalized_result = self._normalize_review_result(result)
        log_payload = review_log_service.create_log(
            db,
            principal=principal,
            review_input=normalized_answer,
            review_result=normalized_result.get("summary") or normalized_result.get("raw_text"),
            raw_response=result.raw,
            normalized_result=normalized_result,
            parse_status=normalized_result["parse_status"],
            score=normalized_result["score"],
            risk_level=normalized_result["risk_level"],
            engine_source="review_dify",
            app_mode=dify_settings.app_mode,
            workflow_run_id=result.workflow_run_id,
            provider_message_id=result.task_id,
        )
        return {
            **normalized_result,
            "review_log_id": log_payload["id"],
            "raw_response": result.raw,
            "rubric_updated_at": rubric.updated_at,
            "source": "review_dify",
            "provider_message_id": result.task_id,
            "workflow_run_id": result.workflow_run_id,
            "created_at": log_payload["created_at"],
        }

    def _serialize_rubric(self, setting: ReviewRubricSetting) -> dict:
        return {
            "rubric_text": setting.rubric_text,
            "updated_at": setting.updated_at,
            "updated_by": setting.updated_by,
            "is_active": setting.is_active,
        }

    def _resolve_review_dify_settings(self, db: Session) -> DifySettings:
        base = settings.review_dify_settings.model_copy()
        runtime = self.review_dify_repo.get_active(db)
        if runtime:
            base.app_mode = runtime.app_mode
            base.response_mode = runtime.response_mode
            base.timeout_seconds = runtime.timeout_seconds
            base.workflow_id = runtime.workflow_id
            base.text_input_variable = runtime.text_input_variable
            base.file_input_variable = runtime.file_input_variable
            base.enable_trace = runtime.enable_trace
            base.user_prefix = runtime.user_prefix
        return base

    @staticmethod
    def _build_review_inputs(*, answer_text: str, rubric_text: str, dify_settings: DifySettings) -> dict[str, str]:
        inputs = {
            "answer_text": answer_text,
            "review_input": answer_text,
            "rubric_text": rubric_text,
        }
        if dify_settings.text_input_variable:
            inputs[dify_settings.text_input_variable] = answer_text
        return inputs

    @staticmethod
    def _build_dify_user(principal: Principal, dify_settings: DifySettings) -> str:
        identity = principal.student_id or principal.username or principal.user_id
        return f"{dify_settings.user_prefix}:{identity}"

    def _normalize_review_result(self, result: DifyWorkflowResult) -> dict:
        raw_text = self._extract_raw_text(result)
        structured_payload = self._extract_structured_payload(result, raw_text)
        data = ReviewResultData().model_dump()

        if structured_payload is None:
            data["summary"] = raw_text or DEFAULT_REVIEW_SUMMARY
            data["raw_text"] = raw_text or None
            data["parse_status"] = "failed"
            return data

        data["score"] = self._normalize_score(structured_payload.get("score"))
        data["grade"] = self._normalize_optional_text(structured_payload.get("grade"))
        data["risk_level"] = self._normalize_risk_level(structured_payload.get("risk_level"))
        data["summary"] = (
            self._normalize_optional_text(structured_payload.get("summary"))
            or self._normalize_optional_text(structured_payload.get("reason"))
            or raw_text
            or DEFAULT_REVIEW_SUMMARY
        )
        data["review_items"] = self._normalize_review_items(structured_payload.get("review_items"))
        data["key_issues"] = self._normalize_key_issues(structured_payload.get("key_issues"))
        data["deduction_logic"] = self._normalize_deduction_logic(structured_payload.get("deduction_logic"))
        data["raw_text"] = raw_text or None

        has_structured_content = bool(
            data["score"] is not None
            or data["grade"]
            or data["risk_level"]
            or data["review_items"]
            or data["key_issues"]
            or data["deduction_logic"]
        )
        data["parse_status"] = "success" if has_structured_content else "partial"
        return data

    def _extract_structured_payload(self, result: DifyWorkflowResult, raw_text: str | None) -> dict | None:
        candidates: list[object] = [result.outputs]
        for value in result.outputs.values():
            candidates.append(value)
        if raw_text:
            candidates.append(raw_text)
        candidates.append(result.raw)

        for candidate in candidates:
            payload = self._coerce_json_object(candidate)
            if payload is not None:
                return payload
        return None

    def _coerce_json_object(self, candidate: object) -> dict | None:
        if isinstance(candidate, dict):
            nested = self._unwrap_useful_dict(candidate)
            if nested:
                return nested
            return candidate if self._looks_like_review_payload(candidate) else None
        if isinstance(candidate, str):
            text = candidate.strip()
            if not text:
                return None
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = self._extract_json_from_text(text)
            if isinstance(parsed, dict):
                nested = self._unwrap_useful_dict(parsed)
                return nested or parsed
        return None

    def _extract_json_from_text(self, text: str) -> dict | None:
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
        if fenced_match:
            try:
                parsed = json.loads(fenced_match.group(1))
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _unwrap_useful_dict(self, payload: dict) -> dict | None:
        if self._looks_like_review_payload(payload):
            return payload
        for key in ("result", "data", "outputs", "review_result"):
            nested = payload.get(key)
            if isinstance(nested, dict) and self._looks_like_review_payload(nested):
                return nested
        return None

    @staticmethod
    def _looks_like_review_payload(payload: dict) -> bool:
        expected_keys = {
            "score",
            "grade",
            "risk_level",
            "summary",
            "review_items",
            "key_issues",
            "deduction_logic",
            "reason",
        }
        return any(key in payload for key in expected_keys)

    def _extract_raw_text(self, result: DifyWorkflowResult) -> str | None:
        preferred = ("text", "answer", "output", "result")
        for key in preferred:
            value = result.outputs.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in result.outputs.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
        answer = result.raw.get("answer")
        if isinstance(answer, str) and answer.strip():
            return answer.strip()
        return None

    def _normalize_review_items(self, value: object) -> list[dict]:
        return [
            {
                "item_name": self._normalize_optional_text(item.get("item_name") or item.get("name")) or "",
                "conclusion": self._normalize_optional_text(item.get("conclusion")) or "",
                "importance": self._normalize_optional_text(item.get("importance")) or "",
                "scheme_excerpt": self._normalize_optional_text(item.get("scheme_excerpt") or item.get("excerpt")) or "",
                "standard_basis": self._normalize_optional_text(item.get("standard_basis") or item.get("basis")) or "",
                "reason": self._normalize_optional_text(item.get("reason")) or "",
                "suggestion": self._normalize_optional_text(item.get("suggestion")) or "",
            }
            for item in self._iter_dict_list(value)
        ]

    def _normalize_key_issues(self, value: object) -> list[dict]:
        return [
            {
                "title": self._normalize_optional_text(item.get("title")) or "",
                "risk_level": self._normalize_risk_level(item.get("risk_level")) or "",
                "problem": self._normalize_optional_text(item.get("problem")) or "",
                "basis": self._normalize_optional_text(item.get("basis")) or "",
                "suggestion": self._normalize_optional_text(item.get("suggestion")) or "",
            }
            for item in self._iter_dict_list(value)
        ]

    def _normalize_deduction_logic(self, value: object) -> list[dict]:
        normalized: list[dict] = []
        for item in self._iter_dict_list(value):
            deducted_score = item.get("deducted_score")
            if isinstance(deducted_score, bool):
                deducted_score = 0
            elif isinstance(deducted_score, str):
                try:
                    deducted_score = float(deducted_score.strip())
                except ValueError:
                    deducted_score = 0
            elif not isinstance(deducted_score, (int, float)):
                deducted_score = 0
            normalized.append(
                {
                    "reason": self._normalize_optional_text(item.get("reason")) or "",
                    "deducted_score": deducted_score,
                }
            )
        return normalized

    @staticmethod
    def _iter_dict_list(value: object) -> Iterable[dict]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _normalize_optional_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _normalize_score(self, raw_score: object) -> int | None:
        if raw_score is None or raw_score == "":
            return None
        if isinstance(raw_score, bool):
            return None
        if isinstance(raw_score, (int, float)):
            normalized = int(round(float(raw_score)))
            return max(0, min(100, normalized))
        if isinstance(raw_score, str):
            try:
                normalized = int(round(float(raw_score.strip())))
            except ValueError:
                return None
            return max(0, min(100, normalized))
        return None

    def _normalize_risk_level(self, value: object) -> str | None:
        text = self._normalize_optional_text(value)
        if not text:
            return None
        normalized = text.lower()
        if normalized in {"高", "高风险", "high", "high_risk"}:
            return "high"
        if normalized in {"中", "中风险", "medium", "medium_risk"}:
            return "medium"
        if normalized in {"低", "低风险", "low", "low_risk"}:
            return "low"
        return text

    def _log_provider_failure(
        self,
        db: Session,
        *,
        principal: Principal,
        review_input: str,
        detail: str,
        error_code: str,
        dify_settings: DifySettings,
    ) -> None:
        review_log_service.create_log(
            db,
            principal=principal,
            review_input=review_input,
            review_result=detail,
            raw_response={"error": detail, "error_code": error_code},
            normalized_result={
                "type": "review_result",
                "score": None,
                "grade": None,
                "risk_level": None,
                "summary": detail,
                "review_items": [],
                "key_issues": [],
                "deduction_logic": [],
                "raw_text": detail,
                "parse_status": "failed",
            },
            parse_status="failed",
            score=None,
            risk_level=None,
            engine_source="review_dify",
            app_mode=dify_settings.app_mode,
            workflow_run_id=None,
            provider_message_id=None,
        )


review_service = ReviewService()
