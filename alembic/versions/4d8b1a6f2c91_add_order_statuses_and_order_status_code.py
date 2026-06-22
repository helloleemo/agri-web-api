"""add order statuses and order status code

Revision ID: 4d8b1a6f2c91
Revises: 71a6f7b09edb
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "4d8b1a6f2c91"
down_revision: Union[str, None] = "71a6f7b09edb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("order_statuses"):
        op.create_table(
            "order_statuses",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("code", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )

    existing_codes = set()
    if inspector.has_table("order_statuses"):
        existing_codes = {row[0] for row in bind.execute(sa.text("SELECT code FROM order_statuses"))}

    order_status_rows = [
        {"id": uuid.UUID("11111111-1111-1111-1111-111111111111"), "code": 1, "name": "訂單成立"},
        {"id": uuid.UUID("22222222-2222-2222-2222-222222222222"), "code": 2, "name": "確認訂單"},
        {"id": uuid.UUID("33333333-3333-3333-3333-333333333333"), "code": 3, "name": "待付款"},
        {"id": uuid.UUID("44444444-4444-4444-4444-444444444444"), "code": 4, "name": "已付款"},
        {"id": uuid.UUID("55555555-5555-5555-5555-555555555555"), "code": 5, "name": "備貨中"},
        {"id": uuid.UUID("66666666-6666-6666-6666-666666666666"), "code": 6, "name": "出貨"},
    ]

    rows_to_insert = [row for row in order_status_rows if row["code"] not in existing_codes]
    if rows_to_insert:
        bind.execute(
            sa.text(
                "INSERT INTO order_statuses (id, code, name) VALUES (:id, :code, :name) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            rows_to_insert,
        )

    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "order_status_code" not in order_columns:
        op.add_column("orders", sa.Column("order_status_code", sa.Integer(), nullable=False, server_default=sa.text("1")))

    existing_indexes = {index["name"] for index in inspector.get_indexes("orders")}
    if "idx_orders_order_status_code" not in existing_indexes:
        op.create_index("idx_orders_order_status_code", "orders", ["order_status_code"], unique=False)

    bind.execute(sa.text("UPDATE orders SET order_status_code = 1 WHERE order_status_code IS NULL"))

    existing_fks = {fk["name"] for fk in inspector.get_foreign_keys("orders")}
    if "orders_order_status_code_fkey" not in existing_fks:
        op.create_foreign_key(
            "orders_order_status_code_fkey",
            "orders",
            "order_statuses",
            ["order_status_code"],
            ["code"],
        )

    op.alter_column("orders", "order_status_code", server_default=None)


def downgrade() -> None:
    op.drop_constraint("orders_order_status_code_fkey", "orders", type_="foreignkey")
    op.drop_index("idx_orders_order_status_code", table_name="orders")
    op.drop_column("orders", "order_status_code")
    op.drop_table("order_statuses")
