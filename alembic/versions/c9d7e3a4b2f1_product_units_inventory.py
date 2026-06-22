"""add product-units inventory mapping

Revision ID: c9d7e3a4b2f1
Revises: 7f20da8282f8
Create Date: 2026-06-03 21:10:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "c9d7e3a4b2f1"
down_revision: Union[str, None] = "7f20da8282f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "units"):
        op.create_table(
            "units",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=20), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if not _has_table(inspector, "product_units"):
        op.create_table(
            "product_units",
            sa.Column("product_id", sa.UUID(), nullable=False),
            sa.Column("unit_id", sa.UUID(), nullable=False),
            sa.Column("price", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
            sa.CheckConstraint("price >= 0", name="ck_product_units_price_non_negative"),
            sa.CheckConstraint("stock >= 0", name="ck_product_units_stock_non_negative"),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("product_id", "unit_id"),
        )
        op.create_index("idx_product_units_unit_id", "product_units", ["unit_id"], unique=False)

        # Remove server defaults after bootstrapping so ORM/application controls values.
        op.alter_column("product_units", "price", server_default=None)
        op.alter_column("product_units", "stock", server_default=None)

    # Refresh inspector after structural changes.
    inspector = sa.inspect(bind)

    has_products = _has_table(inspector, "products")
    has_unit_col = _has_column(inspector, "products", "unit")
    has_unit_id_col = _has_column(inspector, "products", "unit_id")
    has_price_col = _has_column(inspector, "products", "price")
    has_stock_col = _has_column(inspector, "products", "stock")

    if has_products and has_unit_col:
        unit_names = [
            row[0]
            for row in bind.execute(
                text(
                    """
                    SELECT DISTINCT unit
                    FROM products
                    WHERE unit IS NOT NULL AND btrim(unit) <> ''
                    """
                )
            )
        ]
        for name in unit_names:
            bind.execute(
                text(
                    """
                    INSERT INTO units (id, name)
                    VALUES (:id, :name)
                    ON CONFLICT (name) DO NOTHING
                    """
                ),
                {"id": str(uuid.uuid4()), "name": name},
            )

    if has_products and has_unit_col and has_price_col and has_stock_col:
        bind.execute(
            text(
                """
                INSERT INTO product_units (product_id, unit_id, price, stock)
                SELECT p.id, u.id, COALESCE(p.price, 0), COALESCE(p.stock, 0)
                FROM products p
                JOIN units u ON u.name = p.unit
                ON CONFLICT (product_id, unit_id) DO NOTHING
                """
            )
        )

    if has_products and has_unit_id_col:
        bind.execute(
            text(
                """
                INSERT INTO product_units (product_id, unit_id, price, stock)
                SELECT p.id, p.unit_id, COALESCE(p.price, 0), COALESCE(p.stock, 0)
                FROM products p
                WHERE p.unit_id IS NOT NULL
                ON CONFLICT (product_id, unit_id) DO NOTHING
                """
            )
        )

        # Drop foreign keys that reference products.unit_id before dropping the column.
        for fk in inspector.get_foreign_keys("products"):
            constrained_columns = fk.get("constrained_columns") or []
            fk_name = fk.get("name")
            if fk_name and "unit_id" in constrained_columns:
                op.drop_constraint(fk_name, "products", type_="foreignkey")

        op.drop_column("products", "unit_id")

    if has_products and has_unit_col:
        op.drop_column("products", "unit")


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "products") and not _has_column(inspector, "products", "unit"):
        op.add_column("products", sa.Column("unit", sa.String(length=20), nullable=True))

    if _has_table(inspector, "products") and _has_table(inspector, "product_units"):
        bind.execute(
            text(
                """
                UPDATE products p
                SET unit = sub.unit_name
                FROM (
                    SELECT pu.product_id, MIN(u.name) AS unit_name
                    FROM product_units pu
                    JOIN units u ON u.id = pu.unit_id
                    GROUP BY pu.product_id
                ) AS sub
                WHERE p.id = sub.product_id
                """
            )
        )

    inspector = sa.inspect(bind)

    if _has_table(inspector, "product_units"):
        op.drop_index("idx_product_units_unit_id", table_name="product_units")
        op.drop_table("product_units")

    if _has_table(inspector, "units"):
        op.drop_table("units")
