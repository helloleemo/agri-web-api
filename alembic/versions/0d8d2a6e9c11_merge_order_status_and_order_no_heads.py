"""merge order status and order no heads

Revision ID: 0d8d2a6e9c11
Revises: 8d7c2a1f5b3e, 4d8b1a6f2c91
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0d8d2a6e9c11"
down_revision: Union[str, tuple[str, str], None] = ("8d7c2a1f5b3e", "4d8b1a6f2c91")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
