"""user auth tables and qa log identity fields

Revision ID: 20260318_0009
Revises: 20260317_0008
Create Date: 2026-03-18 00:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260318_0009"
down_revision: Union[str, Sequence[str], None] = "20260317_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("student_id", name=op.f("uq_users_student_id")),
    )
    op.create_index(op.f("ix_users_student_id"), "users", ["student_id"], unique=False)

    with op.batch_alter_table("qa_logs") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("student_id_snapshot", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("name_snapshot", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key(op.f("fk_qa_logs_user_id_users"), "users", ["user_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("qa_logs") as batch_op:
        batch_op.drop_constraint(op.f("fk_qa_logs_user_id_users"), type_="foreignkey")
        batch_op.drop_column("name_snapshot")
        batch_op.drop_column("student_id_snapshot")
        batch_op.drop_column("user_id")

    op.drop_index(op.f("ix_users_student_id"), table_name="users")
    op.drop_table("users")
