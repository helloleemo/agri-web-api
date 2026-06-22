"""add email verified at to users

Revision ID: e4a1c2d9f8b7
Revises: 0d8d2a6e9c11
Create Date: 2026-06-11 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4a1c2d9f8b7"
down_revision: Union[str, None] = "0d8d2a6e9c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")