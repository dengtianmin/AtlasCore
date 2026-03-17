"""review rubric settings table

Revision ID: 20260317_0008
Revises: 20260317_0007
Create Date: 2026-03-17 15:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260317_0008"
down_revision: Union[str, Sequence[str], None] = "20260317_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_rubric_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("rubric_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_rubric_settings")),
    )


def downgrade() -> None:
    op.drop_table("review_rubric_settings")
