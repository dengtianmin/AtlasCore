"""graph sqlite compatibility tables

Revision ID: 20260317_0003
Revises: 20260313_0002
Create Date: 2026-03-17 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260317_0003"
down_revision: Union[str, Sequence[str], None] = "20260313_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("node_type", sa.String(length=100), nullable=True),
        sa.Column("source_document", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_nodes")),
    )
    op.create_index(op.f("ix_graph_nodes_node_type"), "graph_nodes", ["node_type"], unique=False)

    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("relation_type", sa.String(length=100), nullable=False),
        sa.Column("relation_label", sa.String(length=255), nullable=True),
        sa.Column("source_document", sa.String(length=255), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_edges")),
    )
    op.create_index(op.f("ix_graph_edges_source_id"), "graph_edges", ["source_id"], unique=False)
    op.create_index(op.f("ix_graph_edges_target_id"), "graph_edges", ["target_id"], unique=False)
    op.create_index(op.f("ix_graph_edges_relation_type"), "graph_edges", ["relation_type"], unique=False)

    op.create_table(
        "graph_sync_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_document_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_sync_records")),
    )

    op.create_table(
        "graph_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("build_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_batch", sa.String(length=255), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_versions")),
    )


def downgrade() -> None:
    op.drop_table("graph_versions")
    op.drop_table("graph_sync_records")
    op.drop_index(op.f("ix_graph_edges_relation_type"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_target_id"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_source_id"), table_name="graph_edges")
    op.drop_table("graph_edges")
    op.drop_index(op.f("ix_graph_nodes_node_type"), table_name="graph_nodes")
    op.drop_table("graph_nodes")
