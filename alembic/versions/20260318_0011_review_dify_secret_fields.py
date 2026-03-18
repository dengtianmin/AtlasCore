"""add review dify base url and api key fields

Revision ID: 20260318_0011
Revises: 20260318_0010
Create Date: 2026-03-18 22:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260318_0011"
down_revision: Union[str, Sequence[str], None] = "20260318_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("review_dify_settings", sa.Column("base_url", sa.Text(), nullable=True))
    op.add_column("review_dify_settings", sa.Column("api_key_ciphertext", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("review_dify_settings", "api_key_ciphertext")
    op.drop_column("review_dify_settings", "base_url")
