from __future__ import annotations

import base64
import hashlib
import json
import re

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.graph_model_setting import GraphModelSetting
from app.models.review_rubric_setting import ReviewRubricSetting
from app.repositories.graph_settings_repo import GraphModelSettingRepository
from app.repositories.review_repo import ReviewRubricSettingRepository

DEFAULT_REVIEW_REASON = "模型未返回有效理由，系统已按当前评分标准生成兜底结果。"


class _LocalSecretBox:
    def __init__(self) -> None:
        seed = settings.JWT_SECRET or settings.ADMIN_AUTH_SECRET or "atlascore-review-model-key"
        self._key = hashlib.sha256(seed.encode("utf-8")).digest()

    def encrypt(self, value: str) -> str:
        raw = value.encode("utf-8")
        cipher = bytes(byte ^ self._key[index % len(self._key)] for index, byte in enumerate(raw))
        return base64.b64encode(cipher).decode("ascii")

    def decrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        raw = base64.b64decode(value.encode("ascii"))
        plain = bytes(byte ^ self._key[index % len(self._key)] for index, byte in enumerate(raw))
        return plain.decode("utf-8")


class ReviewService:
    def __init__(self) -> None:
        self.rubric_repo = ReviewRubricSettingRepository()
        self.model_repo = GraphModelSettingRepository()
        self.secret_box = _LocalSecretBox()

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

    async def evaluate_answer(self, db: Session, *, answer_text: str) -> dict:
        normalized_answer = answer_text.strip()
        if not normalized_answer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Answer text must not be empty")

        rubric = self.rubric_repo.get_active(db)
        if rubric is None or not rubric.rubric_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review rubric is not configured. Please ask an administrator to set it first.",
            )

        model_setting = self._require_active_model(db)
        raw_response = await self._call_model(answer_text=normalized_answer, rubric_text=rubric.rubric_text, model_setting=model_setting)
        parsed = self._parse_review_response(raw_response)
        parsed["rubric_updated_at"] = rubric.updated_at
        return parsed

    def _serialize_rubric(self, setting: ReviewRubricSetting) -> dict:
        return {
            "rubric_text": setting.rubric_text,
            "updated_at": setting.updated_at,
            "updated_by": setting.updated_by,
            "is_active": setting.is_active,
        }

    def _require_active_model(self, db: Session) -> GraphModelSetting:
        setting = self.model_repo.get_active(db)
        if setting is None:
            setting = self._build_model_setting_from_env()
        if setting is None or not setting.enabled:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Review model is not configured")
        resolved = self._resolve_model_runtime_settings(setting)
        if not resolved.api_base_url or not resolved.model_name or not resolved.api_key_ciphertext:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Review model is not fully configured")
        return resolved

    def _build_model_setting_from_env(self) -> GraphModelSetting | None:
        model_name = (settings.GRAPH_EXTRACTION_MODEL_NAME or "").strip()
        api_base_url = (settings.GRAPH_EXTRACTION_MODEL_API_BASE_URL or "").strip()
        api_key = settings.resolved_graph_extraction_model_api_key
        if not model_name and not api_base_url and not api_key and not settings.GRAPH_EXTRACTION_MODEL_ENABLED:
            return None
        return GraphModelSetting(
            provider=settings.GRAPH_EXTRACTION_MODEL_PROVIDER.strip(),
            model_name=model_name or "unset-model",
            api_base_url=api_base_url or None,
            api_key_ciphertext=self.secret_box.encrypt(api_key.strip()) if api_key else None,
            enabled=settings.GRAPH_EXTRACTION_MODEL_ENABLED,
            thinking_enabled=settings.GRAPH_EXTRACTION_MODEL_THINKING_ENABLED,
            is_active=True,
            updated_by="system",
        )

    def _resolve_model_runtime_settings(self, setting: GraphModelSetting) -> GraphModelSetting:
        api_base_url = setting.api_base_url or settings.GRAPH_EXTRACTION_MODEL_API_BASE_URL
        api_key_ciphertext = setting.api_key_ciphertext
        if not api_key_ciphertext:
            fallback_api_key = settings.resolved_graph_extraction_model_api_key
            if fallback_api_key:
                api_key_ciphertext = self.secret_box.encrypt(fallback_api_key)

        return GraphModelSetting(
            id=setting.id,
            provider=setting.provider,
            model_name=setting.model_name,
            api_base_url=api_base_url,
            api_key_ciphertext=api_key_ciphertext,
            enabled=setting.enabled,
            thinking_enabled=setting.thinking_enabled,
            is_active=setting.is_active,
            updated_by=setting.updated_by,
        )

    async def _call_model(self, *, answer_text: str, rubric_text: str, model_setting: GraphModelSetting) -> str:
        api_key = self.secret_box.decrypt(model_setting.api_key_ciphertext)
        if not model_setting.api_base_url or not api_key:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Review model is not fully configured")

        prompt = self._build_prompt(rubric_text=rubric_text, answer_text=answer_text)
        url = f"{model_setting.api_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model_setting.model_name,
            "messages": [
                {"role": "system", "content": "你是一个严格的评阅助手。必须只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        if not model_setting.thinking_enabled:
            payload["thinking"] = {"type": "disabled"}
        try:
            async with httpx.AsyncClient(
                timeout=settings.GRAPH_EXTRACTION_MODEL_TIMEOUT_SECONDS,
                trust_env=False,
            ) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Review model request timed out") from exc
        except httpx.HTTPStatusError as exc:
            response_text = (exc.response.text or "").strip()
            detail = f"Review model request failed with status {exc.response.status_code}"
            if response_text:
                detail = f"{detail}: {response_text[:500]}"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
        except httpx.RequestError as exc:
            detail = str(exc).strip() or repr(exc)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Review model request error: {detail}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Review model returned invalid JSON: {exc}") from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Review model response schema is invalid: {exc}") from exc
        return str(result["choices"][0]["message"]["content"])

    def _build_prompt(self, *, rubric_text: str, answer_text: str) -> str:
        return (
            "请依据以下评分标准对答案打分。"
            "\n\n评分标准：\n"
            f"{rubric_text.strip()}"
            "\n\n待评阅答案：\n"
            f"{answer_text}"
            "\n\n要求：\n"
            "1. 分数范围固定为 0 到 100 的整数。\n"
            "2. 必须结合评分标准说明理由，不能泛泛而谈。\n"
            "3. 只返回合法 JSON，不要输出额外解释。\n"
            '4. JSON 格式必须为：{"score": 0, "reason": "..."}'
        )

    def _parse_review_response(self, raw_text: str) -> dict:
        cleaned = raw_text.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
        if fenced_match:
            cleaned = fenced_match.group(1)

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Review model returned non-JSON content: {exc}") from exc

        if not isinstance(payload, dict):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review model returned an invalid payload")

        score = self._normalize_score(payload.get("score"))
        reason = str(payload.get("reason") or "").strip() or DEFAULT_REVIEW_REASON
        return {"score": score, "reason": reason}

    def _normalize_score(self, raw_score) -> int:
        if isinstance(raw_score, bool):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review model returned an invalid score")
        if isinstance(raw_score, (int, float)):
            normalized = int(round(float(raw_score)))
        elif isinstance(raw_score, str):
            value = raw_score.strip()
            if not value:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review model returned an empty score")
            try:
                normalized = int(round(float(value)))
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review model returned a non-numeric score") from exc
        else:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Review model returned an invalid score")
        return max(0, min(100, normalized))


review_service = ReviewService()
