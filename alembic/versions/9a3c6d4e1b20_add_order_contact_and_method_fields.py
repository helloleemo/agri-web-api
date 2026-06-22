"""add order contact and method fields

Revision ID: 9a3c6d4e1b20
Revises: f2b9b6d5d123
Create Date: 2026-06-13 12:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "9a3c6d4e1b20"
down_revision: Union[str, None] = "f2b9b6d5d123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("customer_name", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("address", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("delivery_method", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("payment_method", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("orderer_name", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("orderer_phone", sa.String(length=20), nullable=True))
    op.add_column("orders", sa.Column("orderer_email", sa.String(length=120), nullable=True))

    op.execute(
        text(
            """
            UPDATE orders o
            SET
                customer_name = COALESCE(o.customer_name, u.user_name),
                delivery_method = COALESCE(o.delivery_method, 1),
                payment_method = COALESCE(o.payment_method, 1),
                orderer_email = COALESCE(o.orderer_email, o.customer_email)
            FROM users u
            WHERE o.user_id = u.id
            """
        )
    )

    op.execute(text("UPDATE orders SET delivery_method = 1 WHERE delivery_method IS NULL"))
    op.execute(text("UPDATE orders SET payment_method = 1 WHERE payment_method IS NULL"))

    op.alter_column("orders", "delivery_method", nullable=False)
    op.alter_column("orders", "payment_method", nullable=False)


def downgrade() -> None:
    op.drop_column("orders", "orderer_email")
    op.drop_column("orders", "orderer_phone")
    op.drop_column("orders", "orderer_name")
    op.drop_column("orders", "payment_method")
    op.drop_column("orders", "delivery_method")
    op.drop_column("orders", "address")
    op.drop_column("orders", "customer_name")
