"""add order manual adjustment amount

Revision ID: 6b2a1c4d5e9f
Revises: 2c7b9f1e4a55, 5c8e7d1a9f20
Create Date: 2026-06-23 16:20:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6b2a1c4d5e9f"
down_revision: Union[str, tuple[str, str], None] = ("2c7b9f1e4a55", "5c8e7d1a9f20")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("orders", "manual_adjustment_amount"):
        op.add_column(
            "orders",
            sa.Column("manual_adjustment_amount", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("orders", "manual_adjustment_amount", server_default=None)


def downgrade() -> None:
    if _has_column("orders", "manual_adjustment_amount"):
        op.drop_column("orders", "manual_adjustment_amount")