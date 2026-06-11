"""add customer email to orders

Revision ID: f2a9d1b4c6e7
Revises: 0d8d2a6e9c11
Create Date: 2026-06-11 21:40:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "f2a9d1b4c6e7"
down_revision: Union[str, None] = "0d8d2a6e9c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.add_column("orders", sa.Column("customer_email", sa.String(length=120), nullable=True))
	op.execute(
		text(
			"""
			UPDATE orders o
			SET customer_email = u.email
			FROM users u
			WHERE o.user_id = u.id
			"""
		)
	)
	op.alter_column("orders", "customer_email", nullable=False)
	op.create_index("idx_orders_customer_email", "orders", ["customer_email"], unique=False)


def downgrade() -> None:
	op.drop_index("idx_orders_customer_email", table_name="orders")
	op.drop_column("orders", "customer_email")
