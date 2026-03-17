"""graph model settings thinking flag

Revision ID: 20260317_0007
Revises: 20260317_0006
Create Date: 2026-03-17 13:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260317_0007"
down_revision: Union[str, Sequence[str], None] = "20260317_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("graph_model_settings") as batch_op:
        batch_op.add_column(sa.Column("thinking_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")))


def downgrade() -> None:
    with op.batch_alter_table("graph_model_settings") as batch_op:
        batch_op.drop_column("thinking_enabled")
