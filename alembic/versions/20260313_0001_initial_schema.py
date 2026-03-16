"""sqlite first initial schema

Revision ID: 20260313_0001
Revises:
Create Date: 2026-03-13 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260313_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_accounts")),
        sa.UniqueConstraint("username", name=op.f("uq_admin_accounts_username")),
    )
    op.create_index(op.f("ix_admin_accounts_username"), "admin_accounts", ["username"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("synced_to_dify", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("synced_to_graph", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["admin_accounts.id"],
            name=op.f("fk_documents_created_by_admin_accounts"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )

    op.create_table(
        "qa_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("retrieved_context", sa.Text(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qa_logs")),
    )
    op.create_index(op.f("ix_qa_logs_session_id"), "qa_logs", ["session_id"], unique=False)

    op.create_table(
        "feedback_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("qa_log_id", sa.String(length=36), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("liked", sa.Boolean(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["qa_log_id"],
            ["qa_logs.id"],
            name=op.f("fk_feedback_records_qa_log_id_qa_logs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback_records")),
    )
    op.create_index(op.f("ix_feedback_records_qa_log_id"), "feedback_records", ["qa_log_id"], unique=False)

    op.create_table(
        "export_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("export_type", sa.String(length=64), nullable=False),
        sa.Column("export_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("operator", sa.String(length=100), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_records")),
    )


def downgrade() -> None:
    op.drop_table("export_records")
    op.drop_index(op.f("ix_feedback_records_qa_log_id"), table_name="feedback_records")
    op.drop_table("feedback_records")
    op.drop_index(op.f("ix_qa_logs_session_id"), table_name="qa_logs")
    op.drop_table("qa_logs")
    op.drop_table("documents")
    op.drop_index(op.f("ix_admin_accounts_username"), table_name="admin_accounts")
    op.drop_table("admin_accounts")
