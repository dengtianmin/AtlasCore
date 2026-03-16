"""step12 integration fields

Revision ID: 20260317_0004
Revises: 20260317_0003
Create Date: 2026-03-17 00:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260317_0004"
down_revision: Union[str, Sequence[str], None] = "20260317_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("qa_logs") as batch_op:
        batch_op.add_column(sa.Column("status", sa.String(length=32), nullable=False, server_default="succeeded"))
        batch_op.add_column(sa.Column("provider_message_id", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("error_code", sa.String(length=64), nullable=True))

    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))
        )
        batch_op.add_column(sa.Column("last_sync_target", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("last_sync_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("last_sync_at")
        batch_op.drop_column("last_sync_status")
        batch_op.drop_column("last_sync_target")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("qa_logs") as batch_op:
        batch_op.drop_column("error_code")
        batch_op.drop_column("provider_message_id")
        batch_op.drop_column("status")
