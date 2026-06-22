"""add admin_note to orders

Revision ID: d3e7f1a2b4c8
Revises: f2b9b6d5d123
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd3e7f1a2b4c8'
down_revision: Union[str, None] = 'f2b9b6d5d123'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('admin_note', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'admin_note')
