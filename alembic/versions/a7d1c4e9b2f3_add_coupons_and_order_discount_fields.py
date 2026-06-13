"""add coupons and order discount fields

Revision ID: a7d1c4e9b2f3
Revises: 9a3c6d4e1b20
Create Date: 2026-06-13 14:10:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


# revision identifiers, used by Alembic.
revision: str = "a7d1c4e9b2f3"
down_revision: Union[str, None] = "9a3c6d4e1b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    existing_tables = inspector.get_table_names()
    order_columns = [col["name"] for col in inspector.get_columns("orders")]

    if "coupons" not in existing_tables:
        op.create_table(
            "coupons",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("discount_type", sa.Integer(), nullable=False),
            sa.Column("discount_value", sa.Integer(), nullable=False),
            sa.Column("min_order_amount", sa.Integer(), nullable=True),
            sa.Column("max_discount_amount", sa.Integer(), nullable=True),
            sa.Column("usage_limit", sa.Integer(), nullable=True),
            sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status_code", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.CheckConstraint("discount_value >= 0", name="ck_coupons_discount_value_non_negative"),
            sa.CheckConstraint("used_count >= 0", name="ck_coupons_used_count_non_negative"),
            sa.ForeignKeyConstraint(["status_code"], ["statuses.code"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("coupons")} if "coupons" in existing_tables else set()

    if "idx_coupons_code" not in existing_indexes:
        op.create_index("idx_coupons_code", "coupons", ["code"], unique=False)
    if "idx_coupons_status_code" not in existing_indexes:
        op.create_index("idx_coupons_status_code", "coupons", ["status_code"], unique=False)
    if "idx_coupons_starts_at" not in existing_indexes:
        op.create_index("idx_coupons_starts_at", "coupons", ["starts_at"], unique=False)
    if "idx_coupons_ends_at" not in existing_indexes:
        op.create_index("idx_coupons_ends_at", "coupons", ["ends_at"], unique=False)

    if "coupon_code" not in order_columns:
        op.add_column("orders", sa.Column("coupon_code", sa.String(length=50), nullable=True))
    if "subtotal_amount" not in order_columns:
        op.add_column("orders", sa.Column("subtotal_amount", sa.Integer(), nullable=True))
    if "discount_amount" not in order_columns:
        op.add_column("orders", sa.Column("discount_amount", sa.Integer(), nullable=True, server_default="0"))
    if "total_amount" not in order_columns:
        op.add_column("orders", sa.Column("total_amount", sa.Integer(), nullable=True))

    order_indexes = {idx["name"] for idx in inspector.get_indexes("orders")}
    if "idx_orders_coupon_code" not in order_indexes:
        op.create_index("idx_orders_coupon_code", "orders", ["coupon_code"], unique=False)

    op.execute("UPDATE orders SET subtotal_amount = 0 WHERE subtotal_amount IS NULL")
    op.execute("UPDATE orders SET discount_amount = 0 WHERE discount_amount IS NULL")
    op.execute("UPDATE orders SET total_amount = COALESCE(subtotal_amount, 0) - COALESCE(discount_amount, 0) WHERE total_amount IS NULL")

    op.alter_column("orders", "subtotal_amount", nullable=False)
    op.alter_column("orders", "discount_amount", nullable=False, server_default=None)
    op.alter_column("orders", "total_amount", nullable=False)


def downgrade() -> None:
    op.drop_index("idx_orders_coupon_code", table_name="orders")
    op.drop_column("orders", "total_amount")
    op.drop_column("orders", "discount_amount")
    op.drop_column("orders", "subtotal_amount")
    op.drop_column("orders", "coupon_code")

    op.drop_index("idx_coupons_ends_at", table_name="coupons")
    op.drop_index("idx_coupons_starts_at", table_name="coupons")
    op.drop_index("idx_coupons_status_code", table_name="coupons")
    op.drop_index("idx_coupons_code", table_name="coupons")
    op.drop_table("coupons")
