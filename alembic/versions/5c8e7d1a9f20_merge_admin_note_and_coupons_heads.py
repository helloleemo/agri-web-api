"""merge admin note and coupons heads

Revision ID: 5c8e7d1a9f20
Revises: a7d1c4e9b2f3, d3e7f1a2b4c8
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5c8e7d1a9f20"
down_revision: Union[str, tuple[str, str], None] = ("a7d1c4e9b2f3", "d3e7f1a2b4c8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass