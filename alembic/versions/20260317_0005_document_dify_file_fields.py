"""document dify file metadata fields

Revision ID: 20260317_0005
Revises: 20260317_0004
Create Date: 2026-03-17 09:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260317_0005"
down_revision: Union[str, Sequence[str], None] = "20260317_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(sa.Column("local_path", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("mime_type", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("file_extension", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("dify_upload_file_id", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("dify_uploaded_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("dify_sync_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("dify_error_code", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("dify_error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("dify_error_message")
        batch_op.drop_column("dify_error_code")
        batch_op.drop_column("dify_sync_status")
        batch_op.drop_column("dify_uploaded_at")
        batch_op.drop_column("dify_upload_file_id")
        batch_op.drop_column("file_extension")
        batch_op.drop_column("mime_type")
        batch_op.drop_column("local_path")
