from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.admin.storage import DocumentStorage
from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.models.document import Document
from app.models.graph_edge import GraphEdge
from app.models.graph_extraction_task import GraphExtractionTask
from app.models.graph_model_setting import GraphModelSetting
from app.models.graph_node import GraphNode, normalize_graph_node_name
from app.models.graph_node_source import GraphNodeSource
from app.models.graph_prompt_setting import GraphPromptSetting
from app.repositories.document_repo import DocumentRepository
from app.repositories.graph_extraction_task_repo import GraphExtractionTaskRepository
from app.repositories.graph_repo import GraphRepository
from app.repositories.graph_settings_repo import GraphModelSettingRepository, GraphPromptSettingRepository
from app.services.graph_service import GraphService

logger = get_logger(__name__)
GRAPH_EXTRACTION_MAX_CHARS_PER_CHUNK = 6000

DEFAULT_GRAPH_EXTRACTION_PROMPT = """\
你是知识图谱抽取器。请从输入 Markdown 中抽取节点和边，并严格返回 JSON。
JSON 格式:
{
  "nodes": [{"name": "...", "node_type": "...", "description": "...", "tags": ["..."]}],
  "edges": [{"source": "...", "target": "...", "relation_type": "...", "relation_label": "..."}]
}
不要输出解释，不要输出 markdown 代码块。
"""


@dataclass(slots=True)
class ExtractedGraphPayload:
    nodes: list[dict]
    edges: list[dict]


class _LocalSecretBox:
    def __init__(self) -> None:
        seed = settings.JWT_SECRET or settings.ADMIN_AUTH_SECRET or "atlascore-graph-model-key"
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


class GraphExtractionService:
    def __init__(self) -> None:
        self.document_repo = DocumentRepository()
        self.task_repo = GraphExtractionTaskRepository()
        self.prompt_repo = GraphPromptSettingRepository()
        self.model_repo = GraphModelSettingRepository()
        self.graph_repo = GraphRepository()
        self.graph_service = GraphService()
        self.storage = DocumentStorage()
        self.secret_box = _LocalSecretBox()

    def list_files(self, db: Session, *, file_type: str, limit: int, offset: int) -> dict:
        items = self.document_repo.list_by_file_type(db, file_type=file_type, limit=limit, offset=offset)
        return {"items": [self._serialize_document(item) for item in items]}

    def upload_file(self, db: Session, *, upload: UploadFile, admin_user_id: UUID, file_type: str) -> dict:
        self._validate_upload(upload, file_type=file_type)
        stored = self.storage.save(upload)
        now = datetime.now(UTC)
        document = self.document_repo.create(
            db,
            filename=upload.filename or "untitled",
            file_type=file_type,
            source_type="upload",
            status="registered" if file_type == "sqlite" else "pending_extraction",
            uploaded_at=now,
            synced_to_dify=False,
            synced_to_graph=False,
            note="SQLite graph snapshot uploaded" if file_type == "sqlite" else "Markdown source registered for graph extraction",
            local_path=stored.local_path,
            source_uri=stored.local_path,
            created_by=admin_user_id,
            mime_type=stored.mime_type,
            content_type=stored.mime_type,
            file_size=stored.file_size,
            file_extension=stored.file_extension,
            dify_sync_status="not_synced",
            created_at=now,
        )
        db.commit()
        log_event(
            logger,
            logging.INFO,
            "graph_file_uploaded",
            "success",
            document_id=str(document.id),
            file_type=file_type,
            filename=document.filename,
        )
        return self._serialize_document(document)

    def delete_md_file(self, db: Session, *, document_id: UUID) -> None:
        document = self._get_document_or_404(db, document_id=document_id)
        if document.file_type != "md":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Markdown files can be deleted here")
        self.storage.delete(document.local_path or document.source_uri)
        self.document_repo.delete(db, doc=document)
        db.commit()

    def activate_sqlite_file(self, db: Session, *, document_id: UUID, operator: str) -> dict:
        document = self._get_document_or_404(db, document_id=document_id)
        if document.file_type != "sqlite":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only SQLite graph files can be activated")
        if not document.local_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SQLite file path is missing")

        payload = self.graph_service.import_graph_sqlite_file(
            file_path=Path(document.local_path),
            filename=document.filename,
            operator=operator,
        )
        document.status = "applied_to_graph"
        document.synced_to_graph = True
        document.last_sync_target = "graph"
        document.last_sync_status = "applied_to_graph"
        document.last_sync_at = datetime.now(UTC)
        document.note = f"Activated graph snapshot version {payload['current_version']}"
        self.document_repo.save(db, doc=document)
        stale_files = self.document_repo.list_by_file_type(db, file_type="sqlite", limit=500, offset=0)
        for item in stale_files:
            if item.id == document.id:
                continue
            if item.status != "superseded":
                item.status = "superseded"
                item.invalidated_at = datetime.now(UTC)
                self.document_repo.save(db, doc=item)
        db.commit()
        return payload

    def list_tasks(self, db: Session, *, limit: int, offset: int) -> dict:
        items = self.task_repo.list_recent(db, limit=limit, offset=offset)
        return {"items": [self._serialize_task(item) for item in items]}

    def get_task(self, db: Session, *, task_id: UUID) -> dict:
        task = self.task_repo.get_by_id(db, task_id=task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction task not found")
        return self._serialize_task(task)

    async def create_extraction_task(self, db: Session, *, document_ids: list[UUID], operator: str) -> dict:
        documents = self.document_repo.list_by_ids(db, document_ids=document_ids)
        if len(documents) != len(document_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Some selected documents do not exist")
        if any(item.file_type != "md" for item in documents):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extraction task only supports Markdown files")

        task = GraphExtractionTask(
            task_type="md_extraction",
            status="extracting",
            selected_document_ids=json.dumps([str(item.id) for item in documents]),
            started_at=datetime.now(UTC),
            operator=operator,
        )
        self.task_repo.create(db, task=task)
        for document in documents:
            document.status = "extracting"
            document.extraction_task_id = task.id
            self.document_repo.save(db, doc=document)
        db.commit()

        try:
            prompt_setting = self._ensure_prompt_setting(db, operator=operator)
            model_setting = self._require_active_model(db)
            extracted_payloads = []
            for document in documents:
                markdown = self._read_document_content(document)
                extracted_payloads.append(
                    await self._extract_single_document(
                        markdown=markdown,
                        document=document,
                        prompt_text=prompt_setting.prompt_text,
                        model_setting=model_setting,
                    )
                )

            version = self._build_graph_version(db, documents=documents, payloads=extracted_payloads, operator=operator)
            task.status = "succeeded"
            task.finished_at = datetime.now(UTC)
            task.output_graph_version = version
            task.result_summary = f"Built graph version {version} from {len(documents)} Markdown files"
            self.task_repo.save(db, task=task)
            for document in documents:
                document.status = "applied_to_graph"
                document.synced_to_graph = True
                document.last_sync_target = "graph"
                document.last_sync_status = "applied_to_graph"
                document.last_sync_at = datetime.now(UTC)
                document.note = f"Included in graph version {version}"
                self.document_repo.save(db, doc=document)

            for document in self.document_repo.list_by_file_type(db, file_type="md", limit=500, offset=0):
                if document.id in {item.id for item in documents}:
                    continue
                if not document.is_active and document.status != "removed_from_current_graph":
                    document.status = "removed_from_current_graph"
                    document.removed_from_graph_at = datetime.now(UTC)
                    self.document_repo.save(db, doc=document)

            db.commit()
            log_event(
                logger,
                logging.INFO,
                "graph_extraction_task_succeeded",
                "success",
                task_id=str(task.id),
                output_graph_version=version,
                document_count=len(documents),
            )
            return self._serialize_task(task)
        except Exception as exc:
            db.rollback()
            task = self.task_repo.get_by_id(db, task_id=task.id) or task
            error_message = self._format_exception_message(exc)
            task.status = "failed"
            task.finished_at = datetime.now(UTC)
            task.error_message = error_message
            self.task_repo.save(db, task=task)
            for document in documents:
                refreshed = self.document_repo.get_by_id(db, document.id)
                if refreshed is None:
                    continue
                refreshed.status = "extraction_failed"
                refreshed.note = error_message
                self.document_repo.save(db, doc=refreshed)
            db.commit()
            log_event(
                logger,
                logging.ERROR,
                "graph_extraction_task_failed",
                "failed",
                task_id=str(task.id),
                detail=error_message,
                error_type=type(exc).__name__,
                error_repr=repr(exc),
                status_code=exc.status_code if isinstance(exc, HTTPException) else None,
            )
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Graph extraction failed: {error_message}") from exc

    def get_prompt_setting(self, db: Session) -> dict:
        setting = self.prompt_repo.get_active(db)
        if setting is None:
            setting = self._ensure_prompt_setting(db, operator="system")
            db.commit()
        return self._serialize_prompt_setting(setting)

    def update_prompt_setting(self, db: Session, *, prompt_text: str, operator: str) -> dict:
        setting = GraphPromptSetting(prompt_text=prompt_text.strip(), updated_by=operator, is_active=True)
        self.prompt_repo.replace_active(db, setting=setting)
        db.commit()
        return self._serialize_prompt_setting(setting)

    def get_model_setting(self, db: Session) -> dict:
        setting = self.model_repo.get_active(db)
        if setting is None:
            setting = self._ensure_model_setting_from_env(db, operator="system")
            if setting is not None:
                db.commit()
                return self._serialize_model_setting(setting)
            return {
                "provider": settings.GRAPH_EXTRACTION_MODEL_PROVIDER,
                "model_name": settings.GRAPH_EXTRACTION_MODEL_NAME or "",
                "api_base_url": settings.GRAPH_EXTRACTION_MODEL_API_BASE_URL,
                "enabled": settings.GRAPH_EXTRACTION_MODEL_ENABLED,
                "thinking_enabled": settings.GRAPH_EXTRACTION_MODEL_THINKING_ENABLED,
                "is_active": False,
                "updated_at": None,
                "updated_by": None,
                "has_api_key": bool(settings.resolved_graph_extraction_model_api_key),
            }
        return self._serialize_model_setting(setting)

    def update_model_setting(
        self,
        db: Session,
        *,
        provider: str,
        model_name: str,
        api_base_url: str | None,
        api_key: str | None,
        enabled: bool,
        thinking_enabled: bool,
        operator: str,
    ) -> dict:
        current = self.model_repo.get_active(db)
        ciphertext = current.api_key_ciphertext if current is not None else None
        if api_key:
            ciphertext = self.secret_box.encrypt(api_key.strip())
        setting = GraphModelSetting(
            provider=provider.strip(),
            model_name=model_name.strip(),
            api_base_url=api_base_url.strip() if api_base_url else None,
            api_key_ciphertext=ciphertext,
            enabled=enabled,
            thinking_enabled=thinking_enabled,
            is_active=True,
            updated_by=operator,
        )
        self.model_repo.replace_active(db, setting=setting)
        db.commit()
        return self._serialize_model_setting(setting)

    def _build_graph_version(
        self,
        db: Session,
        *,
        documents: list[Document],
        payloads: list[ExtractedGraphPayload],
        operator: str,
    ) -> str:
        node_map: dict[tuple[str, str], dict] = {}
        edge_map: dict[tuple[str, str, str], dict] = {}
        document_ids = [str(item.id) for item in documents]

        for document, payload in zip(documents, payloads, strict=True):
            for raw_node in payload.nodes:
                node_name = str(raw_node.get("name", "")).strip()
                if not node_name:
                    continue
                node_type = str(raw_node.get("node_type", "entity")).strip() or "entity"
                normalized = normalize_graph_node_name(node_name)
                key = (normalized, node_type)
                target = node_map.setdefault(
                    key,
                    {
                        "id": f"node_{normalized}_{node_type}",
                        "name": node_name,
                        "normalized_name": normalized,
                        "node_type": node_type,
                        "source_document": document.filename,
                        "description": raw_node.get("description"),
                        "tags": list(dict.fromkeys(raw_node.get("tags") or [])),
                        "metadata": {"supplemental_descriptions": [], "source_documents": [str(document.id)]},
                    },
                )
                description = raw_node.get("description")
                if not target["description"] and description:
                    target["description"] = description
                elif description and description != target["description"]:
                    target["metadata"]["supplemental_descriptions"].append(description)
                target["tags"] = list(dict.fromkeys([*target["tags"], *(raw_node.get("tags") or [])]))
                target["metadata"]["source_documents"] = list(
                    dict.fromkeys([*target["metadata"]["source_documents"], str(document.id)])
                )

            for raw_edge in payload.edges:
                source_name = str(raw_edge.get("source", "")).strip()
                target_name = str(raw_edge.get("target", "")).strip()
                relation_type = str(raw_edge.get("relation_type", "")).strip()
                if not source_name or not target_name or not relation_type:
                    continue
                source_key = (normalize_graph_node_name(source_name), str(raw_edge.get("source_type", "entity")).strip() or "entity")
                target_key = (normalize_graph_node_name(target_name), str(raw_edge.get("target_type", "entity")).strip() or "entity")
                source_node = node_map.setdefault(
                    source_key,
                    {
                        "id": f"node_{source_key[0]}_{source_key[1]}",
                        "name": source_name,
                        "normalized_name": source_key[0],
                        "node_type": source_key[1],
                        "source_document": document.filename,
                        "description": None,
                        "tags": [],
                        "metadata": {"supplemental_descriptions": [], "source_documents": [str(document.id)]},
                    },
                )
                target_node = node_map.setdefault(
                    target_key,
                    {
                        "id": f"node_{target_key[0]}_{target_key[1]}",
                        "name": target_name,
                        "normalized_name": target_key[0],
                        "node_type": target_key[1],
                        "source_document": document.filename,
                        "description": None,
                        "tags": [],
                        "metadata": {"supplemental_descriptions": [], "source_documents": [str(document.id)]},
                    },
                )
                edge_key = (source_node["id"], target_node["id"], relation_type)
                edge_map.setdefault(
                    edge_key,
                    {
                        "id": f"edge_{hashlib.md5('|'.join(edge_key).encode('utf-8')).hexdigest()}",
                        "source_id": source_node["id"],
                        "target_id": target_node["id"],
                        "relation_type": relation_type,
                        "relation_label": raw_edge.get("relation_label"),
                        "source_document": document.filename,
                        "source_document_id": str(document.id),
                        "weight": None,
                        "metadata": {},
                    },
                )

        now = datetime.now(UTC)
        nodes = [
            GraphNode(
                id=item["id"],
                name=item["name"],
                normalized_name=item["normalized_name"],
                node_type=item["node_type"],
                source_document=item["source_document"],
                description=item["description"],
                tags_json=json.dumps(item["tags"], ensure_ascii=True),
                metadata_json=json.dumps(item["metadata"], ensure_ascii=True),
                created_at=now,
                updated_at=now,
            )
            for item in node_map.values()
        ]
        node_sources = []
        for item in node_map.values():
            for document_id in item["metadata"]["source_documents"]:
                node_sources.append(
                    GraphNodeSource(
                        id=f"ns_{hashlib.md5(f'{item['id']}|{document_id}'.encode('utf-8')).hexdigest()}",
                        node_id=item["id"],
                        document_id=document_id,
                        source_ref=None,
                        created_at=now,
                        updated_at=now,
                    )
                )
        edges = [
            GraphEdge(
                id=item["id"],
                source_id=item["source_id"],
                target_id=item["target_id"],
                relation_type=item["relation_type"],
                relation_label=item["relation_label"],
                source_document=item["source_document"],
                source_document_id=item["source_document_id"],
                weight=item["weight"],
                metadata_json=json.dumps(item["metadata"], ensure_ascii=True),
                created_at=now,
                updated_at=now,
            )
            for item in edge_map.values()
        ]

        graph_session = self.graph_service.get_graph_session()
        try:
            self.graph_repo.replace_graph_contents(graph_session, nodes=nodes, node_sources=node_sources, edges=edges)
            version = now.strftime("extract_%Y%m%d%H%M%S")
            self.graph_repo.replace_current_version(
                graph_session,
                version=version,
                version_type="md_extraction",
                build_time=now,
                source_batch="markdown",
                source_document_ids=document_ids,
                note=f"Built from {len(documents)} Markdown files",
                operator=operator,
            )
            graph_session.commit()
        finally:
            graph_session.close()

        self.graph_service.reload_graph()
        return version

    async def _extract_single_document(
        self,
        *,
        markdown: str,
        document: Document,
        prompt_text: str,
        model_setting: GraphModelSetting,
    ) -> ExtractedGraphPayload:
        chunk_payloads: list[ExtractedGraphPayload] = []
        chunks = self._split_markdown_into_chunks(markdown)
        for chunk_index, chunk in enumerate(chunks, start=1):
            response_text = await self._call_model(
                prompt_text=prompt_text,
                markdown=chunk,
                model_setting=model_setting,
            )
            payload = self._parse_extraction_payload(response_text)
            chunk_payloads.append(payload)
            log_event(
                logger,
                logging.INFO,
                "graph_document_chunk_extracted",
                "success",
                document_id=str(document.id),
                chunk_index=chunk_index,
                chunk_count=len(chunks),
                node_count=len(payload.nodes),
                edge_count=len(payload.edges),
            )
        payload = self._merge_extracted_payloads(chunk_payloads)
        log_event(
            logger,
            logging.INFO,
            "graph_document_extracted",
            "success",
            document_id=str(document.id),
            chunk_count=len(chunks),
            node_count=len(payload.nodes),
            edge_count=len(payload.edges),
        )
        return payload

    async def _call_model(self, *, prompt_text: str, markdown: str, model_setting: GraphModelSetting) -> str:
        resolved_model_setting = self._resolve_model_runtime_settings(model_setting)
        api_key = self.secret_box.decrypt(resolved_model_setting.api_key_ciphertext)
        if not resolved_model_setting.api_base_url or not api_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Graph extraction model is not fully configured")

        base_url = resolved_model_setting.api_base_url.rstrip("/")
        url = f"{base_url}/chat/completions"
        payload = {
            "model": resolved_model_setting.model_name,
            "messages": [
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": markdown},
            ],
            "temperature": 0,
        }
        if not resolved_model_setting.thinking_enabled:
            payload["thinking"] = {"type": "disabled"}
        try:
            async with httpx.AsyncClient(timeout=settings.DIFY_TIMEOUT_SECONDS, trust_env=False) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Graph extraction model request timed out: {type(exc).__name__}",
            ) from exc
        except httpx.HTTPStatusError as exc:
            response_text = (exc.response.text or "").strip()
            detail = f"Graph extraction model request failed with status {exc.response.status_code}"
            if response_text:
                detail = f"{detail}: {response_text[:500]}"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
        except httpx.RequestError as exc:
            detail = str(exc).strip() or repr(exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Graph extraction model request error ({type(exc).__name__}): {detail}",
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Graph extraction model returned invalid JSON: {exc}",
            ) from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Graph extraction model response schema is invalid: {exc}",
            ) from exc
        return str(result["choices"][0]["message"]["content"])

    def _parse_extraction_payload(self, raw_text: str) -> ExtractedGraphPayload:
        cleaned = raw_text.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
        if fenced_match:
            cleaned = fenced_match.group(1)
        payload = json.loads(cleaned)
        return ExtractedGraphPayload(nodes=list(payload.get("nodes") or []), edges=list(payload.get("edges") or []))

    def _merge_extracted_payloads(self, payloads: list[ExtractedGraphPayload]) -> ExtractedGraphPayload:
        merged_nodes: list[dict] = []
        merged_edges: list[dict] = []
        for payload in payloads:
            merged_nodes.extend(payload.nodes)
            merged_edges.extend(payload.edges)
        return ExtractedGraphPayload(nodes=merged_nodes, edges=merged_edges)

    def _split_markdown_into_chunks(self, markdown: str, *, max_chars: int = GRAPH_EXTRACTION_MAX_CHARS_PER_CHUNK) -> list[str]:
        text = markdown.strip()
        if not text:
            return [""]
        if len(text) <= max_chars:
            return [text]

        sections = [section.strip() for section in re.split(r"(?m)(?=^#{1,6}\s+)", text) if section.strip()]
        if not sections:
            sections = [text]

        chunks: list[str] = []
        current_parts: list[str] = []
        current_length = 0

        for section in sections:
            for piece in self._split_section_to_pieces(section, max_chars=max_chars):
                piece_length = len(piece)
                separator_length = 2 if current_parts else 0
                if current_parts and current_length + separator_length + piece_length > max_chars:
                    chunks.append("\n\n".join(current_parts))
                    current_parts = [piece]
                    current_length = piece_length
                    continue
                current_parts.append(piece)
                current_length += separator_length + piece_length

        if current_parts:
            chunks.append("\n\n".join(current_parts))
        return chunks or [text]

    def _split_section_to_pieces(self, section: str, *, max_chars: int) -> list[str]:
        if len(section) <= max_chars:
            return [section]

        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", section) if paragraph.strip()]
        if len(paragraphs) <= 1:
            return self._hard_split_text(section, max_chars=max_chars)

        pieces: list[str] = []
        current_parts: list[str] = []
        current_length = 0

        for paragraph in paragraphs:
            if len(paragraph) > max_chars:
                if current_parts:
                    pieces.append("\n\n".join(current_parts))
                    current_parts = []
                    current_length = 0
                pieces.extend(self._hard_split_text(paragraph, max_chars=max_chars))
                continue

            separator_length = 2 if current_parts else 0
            if current_parts and current_length + separator_length + len(paragraph) > max_chars:
                pieces.append("\n\n".join(current_parts))
                current_parts = [paragraph]
                current_length = len(paragraph)
                continue

            current_parts.append(paragraph)
            current_length += separator_length + len(paragraph)

        if current_parts:
            pieces.append("\n\n".join(current_parts))
        return pieces

    def _hard_split_text(self, text: str, *, max_chars: int) -> list[str]:
        pieces: list[str] = []
        remaining = text.strip()
        while len(remaining) > max_chars:
            split_at = remaining.rfind("\n", 0, max_chars)
            if split_at <= 0:
                split_at = remaining.rfind(" ", 0, max_chars)
            if split_at <= 0:
                split_at = max_chars
            pieces.append(remaining[:split_at].strip())
            remaining = remaining[split_at:].strip()
        if remaining:
            pieces.append(remaining)
        return pieces

    def _serialize_document(self, document: Document) -> dict:
        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "source_type": document.source_type,
            "status": document.status,
            "uploaded_at": document.uploaded_at,
            "synced_to_dify": document.synced_to_dify,
            "synced_to_graph": document.synced_to_graph,
            "note": document.note,
            "local_path": document.local_path,
            "source_uri": document.source_uri,
            "mime_type": document.mime_type,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "file_extension": document.file_extension,
            "created_by": document.created_by,
            "created_at": document.created_at,
            "last_sync_target": document.last_sync_target,
            "last_sync_status": document.last_sync_status,
            "last_sync_at": document.last_sync_at,
            "removed_from_graph_at": document.removed_from_graph_at,
            "invalidated_at": document.invalidated_at,
            "is_active": document.is_active,
            "extraction_task_id": document.extraction_task_id,
        }

    def _serialize_task(self, task: GraphExtractionTask) -> dict:
        return {
            "id": task.id,
            "task_type": task.task_type,
            "status": task.status,
            "selected_document_ids": json.loads(task.selected_document_ids),
            "started_at": task.started_at,
            "finished_at": task.finished_at,
            "error_message": task.error_message,
            "result_summary": task.result_summary,
            "output_graph_version": task.output_graph_version,
            "operator": task.operator,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

    def _serialize_prompt_setting(self, setting: GraphPromptSetting) -> dict:
        return {
            "prompt_text": setting.prompt_text,
            "updated_at": setting.updated_at,
            "updated_by": setting.updated_by,
            "is_active": setting.is_active,
        }

    def _serialize_model_setting(self, setting: GraphModelSetting) -> dict:
        return {
            "provider": setting.provider,
            "model_name": setting.model_name,
            "api_base_url": setting.api_base_url,
            "enabled": setting.enabled,
            "thinking_enabled": setting.thinking_enabled,
            "is_active": setting.is_active,
            "updated_at": setting.updated_at,
            "updated_by": setting.updated_by,
            "has_api_key": bool(setting.api_key_ciphertext),
        }

    def _ensure_prompt_setting(self, db: Session, *, operator: str) -> GraphPromptSetting:
        setting = self.prompt_repo.get_active(db)
        if setting is not None:
            return setting
        setting = GraphPromptSetting(
            prompt_text=settings.GRAPH_EXTRACTION_PROMPT or DEFAULT_GRAPH_EXTRACTION_PROMPT,
            updated_by=operator,
            is_active=True,
        )
        self.prompt_repo.replace_active(db, setting=setting)
        return setting

    def _require_active_model(self, db: Session) -> GraphModelSetting:
        setting = self.model_repo.get_active(db)
        if setting is None:
            setting = self._ensure_model_setting_from_env(db, operator="system")
            if setting is not None:
                db.commit()
        if setting is None or not setting.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Graph extraction model is not configured")
        return self._resolve_model_runtime_settings(setting)

    def _ensure_model_setting_from_env(self, db: Session, *, operator: str) -> GraphModelSetting | None:
        model_name = (settings.GRAPH_EXTRACTION_MODEL_NAME or "").strip()
        api_base_url = (settings.GRAPH_EXTRACTION_MODEL_API_BASE_URL or "").strip()
        api_key = settings.resolved_graph_extraction_model_api_key
        if not model_name and not api_base_url and not api_key and not settings.GRAPH_EXTRACTION_MODEL_ENABLED:
            return None

        setting = GraphModelSetting(
            provider=settings.GRAPH_EXTRACTION_MODEL_PROVIDER.strip(),
            model_name=model_name or "unset-model",
            api_base_url=api_base_url or None,
            api_key_ciphertext=self.secret_box.encrypt(api_key.strip()) if api_key else None,
            enabled=settings.GRAPH_EXTRACTION_MODEL_ENABLED,
            thinking_enabled=settings.GRAPH_EXTRACTION_MODEL_THINKING_ENABLED,
            is_active=True,
            updated_by=operator,
        )
        self.model_repo.replace_active(db, setting=setting)
        return setting

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
            created_at=setting.created_at,
            updated_at=setting.updated_at,
        )

    def _format_exception_message(self, exc: Exception) -> str:
        if isinstance(exc, HTTPException):
            detail = exc.detail
            if isinstance(detail, str) and detail.strip():
                return detail
            return f"{type(exc).__name__}(status_code={exc.status_code})"
        text = str(exc).strip()
        if text:
            return text
        return repr(exc)

    def _get_document_or_404(self, db: Session, *, document_id: UUID) -> Document:
        document = self.document_repo.get_by_id(db, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def _read_document_content(self, document: Document) -> str:
        path = Path(document.local_path or document.source_uri or "")
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source file missing for document {document.id}")
        return path.read_text(encoding="utf-8")

    def _validate_upload(self, upload: UploadFile, *, file_type: str) -> None:
        filename = (upload.filename or "").strip()
        if not filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a filename")
        suffix = Path(filename).suffix.lower()
        expected = {".md", ".markdown"} if file_type == "md" else {".db", ".sqlite", ".sqlite3"}
        if suffix not in expected:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported {file_type} file type")


graph_extraction_service = GraphExtractionService()
