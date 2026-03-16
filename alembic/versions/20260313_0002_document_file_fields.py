"""schema alignment noop for sqlite first baseline

Revision ID: 20260313_0002
Revises: 20260313_0001
Create Date: 2026-03-13 00:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260313_0002"
down_revision: Union[str, Sequence[str], None] = "20260313_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
