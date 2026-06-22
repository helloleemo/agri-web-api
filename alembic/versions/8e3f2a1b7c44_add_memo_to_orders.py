"""add memo to orders

Revision ID: 8e3f2a1b7c44
Revises: 5c8e7d1a9f20
Create Date: 2026-06-19 07:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e3f2a1b7c44"
down_revision: Union[str, tuple[str, str], None] = "5c8e7d1a9f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("memo", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "memo")