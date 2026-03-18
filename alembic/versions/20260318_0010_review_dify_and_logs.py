"""review dify settings and logs

Revision ID: 20260318_0010
Revises: 20260318_0009
Create Date: 2026-03-18 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260318_0010"
down_revision: Union[str, Sequence[str], None] = "20260318_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_dify_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("app_mode", sa.String(length=32), nullable=False),
        sa.Column("response_mode", sa.String(length=32), nullable=False),
        sa.Column("timeout_seconds", sa.Float(), nullable=False),
        sa.Column("workflow_id", sa.String(length=255), nullable=True),
        sa.Column("text_input_variable", sa.String(length=128), nullable=True),
        sa.Column("file_input_variable", sa.String(length=128), nullable=True),
        sa.Column("enable_trace", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("user_prefix", sa.String(length=64), nullable=False, server_default="review"),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_dify_settings")),
    )

    op.create_table(
        "review_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("student_id_snapshot", sa.String(length=10), nullable=True),
        sa.Column("name_snapshot", sa.String(length=50), nullable=True),
        sa.Column("review_input", sa.Text(), nullable=False),
        sa.Column("review_result", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("normalized_result", sa.Text(), nullable=True),
        sa.Column("parse_status", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.String(length=32), nullable=True),
        sa.Column("engine_source", sa.String(length=64), nullable=False),
        sa.Column("app_mode", sa.String(length=32), nullable=True),
        sa.Column("workflow_run_id", sa.String(length=128), nullable=True),
        sa.Column("provider_message_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_review_logs_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_logs")),
    )


def downgrade() -> None:
    op.drop_table("review_logs")
    op.drop_table("review_dify_settings")
