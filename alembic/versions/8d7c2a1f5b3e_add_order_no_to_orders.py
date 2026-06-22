"""add order no to orders

Revision ID: 8d7c2a1f5b3e
Revises: 71a6f7b09edb
Create Date: 2026-06-04 21:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "8d7c2a1f5b3e"
down_revision: Union[str, None] = "71a6f7b09edb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.add_column("orders", sa.Column("order_no", sa.String(length=20), nullable=True))

	op.execute(
		text(
			"""
			WITH ordered_orders AS (
				SELECT
					o.id,
					'OC' || to_char(o.created_at, 'YYYYMMDD') || lpad(
						row_number() OVER (
							PARTITION BY to_char(o.created_at, 'YYYYMMDD')
							ORDER BY o.created_at, o.id
						)::text,
						6,
						'0'
					) AS order_no
				FROM orders o
			)
			UPDATE orders AS target
			SET order_no = ordered_orders.order_no
			FROM ordered_orders
			WHERE target.id = ordered_orders.id
			"""
		)
	)

	op.alter_column("orders", "order_no", nullable=False)
	op.create_unique_constraint("uq_orders_order_no", "orders", ["order_no"])


def downgrade() -> None:
	op.drop_constraint("uq_orders_order_no", "orders", type_="unique")
	op.drop_column("orders", "order_no")