from datetime import datetime
import json

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.models.graph_node_source import GraphNodeSource
from app.models.graph_sync_record import GraphSyncRecord
from app.models.graph_version import GraphVersion


class GraphRepository:
    def fetch_all_nodes(self, db: Session) -> list[GraphNode]:
        stmt = select(GraphNode).order_by(GraphNode.name.asc(), GraphNode.id.asc())
        return list(db.execute(stmt).scalars().all())

    def fetch_all_edges(self, db: Session) -> list[GraphEdge]:
        stmt = select(GraphEdge).order_by(GraphEdge.id.asc())
        return list(db.execute(stmt).scalars().all())

    def list_nodes(
        self,
        db: Session,
        *,
        limit: int,
        offset: int,
        node_type: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list[GraphNode], int]:
        stmt = select(GraphNode)
        if node_type:
            stmt = stmt.where(GraphNode.node_type == node_type)
        if keyword:
            like_value = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    GraphNode.id.ilike(like_value),
                    GraphNode.name.ilike(like_value),
                    GraphNode.description.ilike(like_value),
                    GraphNode.source_document.ilike(like_value),
                )
            )

        all_items = list(db.execute(stmt.order_by(GraphNode.name.asc(), GraphNode.id.asc())).scalars().all())
        return all_items[offset : offset + limit], len(all_items)

    def get_node(self, db: Session, *, node_id: str) -> GraphNode | None:
        return db.get(GraphNode, node_id)

    def list_node_sources(self, db: Session, *, node_id: str) -> list[GraphNodeSource]:
        stmt = (
            select(GraphNodeSource)
            .where(GraphNodeSource.node_id == node_id)
            .order_by(GraphNodeSource.document_id.asc(), GraphNodeSource.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_current_version(self, db: Session) -> GraphVersion | None:
        stmt = select(GraphVersion).where(GraphVersion.is_current.is_(True)).order_by(GraphVersion.imported_at.desc())
        return db.execute(stmt).scalar_one_or_none()

    def replace_current_version(
        self,
        db: Session,
        *,
        version: str,
        build_time: datetime | None = None,
        source_batch: str | None = None,
        exported_at: datetime | None = None,
        imported_at: datetime | None = None,
        note: str | None = None,
        version_type: str | None = None,
        source_document_ids: list[str] | None = None,
        operator: str | None = None,
    ) -> GraphVersion:
        db.execute(update(GraphVersion).values(is_current=False))
        record = GraphVersion(
            version=version,
            version_type=version_type,
            build_time=build_time,
            source_batch=source_batch,
            source_document_ids=json.dumps(source_document_ids or []),
            exported_at=exported_at,
            imported_at=imported_at,
            note=note,
            operator=operator,
            is_current=True,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

    def create_sync_record(
        self,
        db: Session,
        *,
        status: str,
        started_at: datetime,
        source_document_id: str | None = None,
        finished_at: datetime | None = None,
        error_message: str | None = None,
        summary: str | None = None,
    ) -> GraphSyncRecord:
        record = GraphSyncRecord(
            source_document_id=source_document_id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            error_message=error_message,
            summary=summary,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        return record

    def replace_graph_contents(
        self,
        db: Session,
        *,
        nodes: list[GraphNode],
        node_sources: list[GraphNodeSource],
        edges: list[GraphEdge],
    ) -> None:
        db.execute(delete(GraphNodeSource))
        db.execute(delete(GraphEdge))
        db.execute(delete(GraphNode))
        for item in nodes:
            db.add(item)
        for item in node_sources:
            db.add(item)
        for item in edges:
            db.add(item)
        db.flush()

    def clear_graph_contents(self, db: Session) -> None:
        db.execute(delete(GraphNodeSource))
        db.execute(delete(GraphEdge))
        db.execute(delete(GraphNode))
        db.execute(delete(GraphSyncRecord))
        db.execute(delete(GraphVersion))
        db.flush()
