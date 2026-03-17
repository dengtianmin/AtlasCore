"""graph extraction management tables and document metadata fields

Revision ID: 20260317_0006
Revises: 20260317_0005
Create Date: 2026-03-17 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260317_0006"
down_revision: Union[str, Sequence[str], None] = "20260317_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(sa.Column("file_type", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("extraction_task_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("removed_from_graph_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")))

    op.execute(
        """
        UPDATE documents
        SET file_type = CASE
            WHEN LOWER(COALESCE(file_extension, '')) IN ('md', 'markdown') THEN 'md'
            WHEN LOWER(COALESCE(file_extension, '')) IN ('db', 'sqlite', 'sqlite3') THEN 'sqlite'
            ELSE 'generic'
        END
        """
    )

    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column("file_type", existing_type=sa.String(length=32), nullable=False)

    op.create_table(
        "graph_extraction_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("selected_document_ids", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("output_graph_version", sa.String(length=64), nullable=True),
        sa.Column("operator", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_extraction_tasks")),
    )
    op.create_table(
        "graph_prompt_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_prompt_settings")),
    )
    op.create_table(
        "graph_model_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("api_base_url", sa.Text(), nullable=True),
        sa.Column("api_key_ciphertext", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_model_settings")),
    )


def downgrade() -> None:
    op.drop_table("graph_model_settings")
    op.drop_table("graph_prompt_settings")
    op.drop_table("graph_extraction_tasks")
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("invalidated_at")
        batch_op.drop_column("removed_from_graph_at")
        batch_op.drop_column("extraction_task_id")
        batch_op.drop_column("file_type")
