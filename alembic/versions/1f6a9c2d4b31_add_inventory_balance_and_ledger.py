"""add inventory balance and ledger tables

Revision ID: 1f6a9c2d4b31
Revises: 8e3f2a1b7c44
Create Date: 2026-06-22 12:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "1f6a9c2d4b31"
down_revision: Union[str, tuple[str, str], None] = "8e3f2a1b7c44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "inventory_balances"):
        op.create_table(
            "inventory_balances",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("product_id", sa.UUID(), nullable=False),
            sa.Column("unit_id", sa.UUID(), nullable=False),
            sa.Column("initial_stock", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("actual_stock", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reserved_stock", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("manual_adjustment_stock", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("initial_stock >= 0", name="ck_inventory_balances_initial_non_negative"),
            sa.CheckConstraint("actual_stock >= 0", name="ck_inventory_balances_actual_non_negative"),
            sa.CheckConstraint("reserved_stock >= 0", name="ck_inventory_balances_reserved_non_negative"),
            sa.CheckConstraint("actual_stock >= reserved_stock", name="ck_inventory_balances_actual_gte_reserved"),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("product_id", "unit_id", name="uq_inventory_balances_product_unit"),
        )
        op.create_index("idx_inventory_balances_product_id", "inventory_balances", ["product_id"], unique=False)
        op.create_index("idx_inventory_balances_unit_id", "inventory_balances", ["unit_id"], unique=False)

        op.alter_column("inventory_balances", "initial_stock", server_default=None)
        op.alter_column("inventory_balances", "actual_stock", server_default=None)
        op.alter_column("inventory_balances", "reserved_stock", server_default=None)
        op.alter_column("inventory_balances", "manual_adjustment_stock", server_default=None)

    if not _has_table(inspector, "inventory_ledger"):
        op.create_table(
            "inventory_ledger",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("product_id", sa.UUID(), nullable=False),
            sa.Column("unit_id", sa.UUID(), nullable=False),
            sa.Column("order_id", sa.UUID(), nullable=True),
            sa.Column("order_item_id", sa.UUID(), nullable=True),
            sa.Column("action", sa.String(length=32), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("delta_actual", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("delta_reserved", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("actual_after", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reserved_after", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("available_after", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("from_order_status_code", sa.Integer(), nullable=True),
            sa.Column("to_order_status_code", sa.Integer(), nullable=True),
            sa.Column("operator_user_id", sa.UUID(), nullable=True),
            sa.Column("note", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
            sa.ForeignKeyConstraint(["operator_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_inventory_ledger_product_unit", "inventory_ledger", ["product_id", "unit_id"], unique=False)
        op.create_index("idx_inventory_ledger_order_item", "inventory_ledger", ["order_item_id"], unique=False)
        op.create_index("idx_inventory_ledger_created_at", "inventory_ledger", ["created_at"], unique=False)
        op.create_index("idx_inventory_ledger_operator_user_id", "inventory_ledger", ["operator_user_id"], unique=False)

        op.alter_column("inventory_ledger", "quantity", server_default=None)
        op.alter_column("inventory_ledger", "delta_actual", server_default=None)
        op.alter_column("inventory_ledger", "delta_reserved", server_default=None)
        op.alter_column("inventory_ledger", "actual_after", server_default=None)
        op.alter_column("inventory_ledger", "reserved_after", server_default=None)
        op.alter_column("inventory_ledger", "available_after", server_default=None)

    inspector = sa.inspect(bind)

    if _has_table(inspector, "order_items") and not _has_column(inspector, "order_items", "unit"):
        op.add_column("order_items", sa.Column("unit", sa.String(length=20), nullable=True))

    if _has_table(inspector, "order_items") and not _has_column(inspector, "order_items", "unit_id"):
        op.add_column("order_items", sa.Column("unit_id", sa.UUID(), nullable=True))
        op.create_foreign_key("fk_order_items_unit_id_units", "order_items", "units", ["unit_id"], ["id"])

    if _has_table(inspector, "product_units") and _has_table(inspector, "inventory_balances"):
        rows = list(
            bind.execute(
                text(
                    """
                    SELECT pu.product_id, pu.unit_id, COALESCE(pu.stock, 0) AS stock
                    FROM product_units pu
                    """
                )
            )
        )
        for product_id, unit_id, stock in rows:
            bind.execute(
                text(
                    """
                    INSERT INTO inventory_balances (
                        id, product_id, unit_id, initial_stock, actual_stock, reserved_stock, manual_adjustment_stock
                    )
                    VALUES (:id, :product_id, :unit_id, :initial_stock, :actual_stock, 0, 0)
                    ON CONFLICT (product_id, unit_id) DO NOTHING
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "product_id": str(product_id),
                    "unit_id": str(unit_id),
                    "initial_stock": int(stock or 0),
                    "actual_stock": int(stock or 0),
                },
            )

    if _has_table(inspector, "inventory_balances") and _has_table(inspector, "inventory_ledger"):
        rows = list(
            bind.execute(
                text(
                    """
                    SELECT product_id, unit_id, initial_stock, actual_stock, reserved_stock
                    FROM inventory_balances
                    WHERE initial_stock > 0
                    """
                )
            )
        )
        for product_id, unit_id, initial_stock, actual_stock, reserved_stock in rows:
            bind.execute(
                text(
                    """
                    INSERT INTO inventory_ledger (
                        id, product_id, unit_id, order_id, order_item_id,
                        action, quantity, delta_actual, delta_reserved,
                        actual_after, reserved_after, available_after,
                        from_order_status_code, to_order_status_code,
                        operator_user_id, note
                    )
                    VALUES (
                        :id, :product_id, :unit_id, NULL, NULL,
                        'INITIALIZE', :quantity, :delta_actual, 0,
                        :actual_after, :reserved_after, :available_after,
                        NULL, NULL,
                        NULL, :note
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "product_id": str(product_id),
                    "unit_id": str(unit_id),
                    "quantity": int(initial_stock),
                    "delta_actual": int(initial_stock),
                    "actual_after": int(actual_stock),
                    "reserved_after": int(reserved_stock),
                    "available_after": int(actual_stock) - int(reserved_stock),
                    "note": "Backfilled from product_units.stock during migration",
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "order_items") and _has_column(inspector, "order_items", "unit_id"):
        op.drop_constraint("fk_order_items_unit_id_units", "order_items", type_="foreignkey")
        op.drop_column("order_items", "unit_id")

    if _has_table(inspector, "order_items") and _has_column(inspector, "order_items", "unit"):
        op.drop_column("order_items", "unit")

    if _has_table(inspector, "inventory_ledger"):
        op.drop_index("idx_inventory_ledger_operator_user_id", table_name="inventory_ledger")
        op.drop_index("idx_inventory_ledger_created_at", table_name="inventory_ledger")
        op.drop_index("idx_inventory_ledger_order_item", table_name="inventory_ledger")
        op.drop_index("idx_inventory_ledger_product_unit", table_name="inventory_ledger")
        op.drop_table("inventory_ledger")

    if _has_table(inspector, "inventory_balances"):
        op.drop_index("idx_inventory_balances_unit_id", table_name="inventory_balances")
        op.drop_index("idx_inventory_balances_product_id", table_name="inventory_balances")
        op.drop_table("inventory_balances")
