"""add order shipping fee transfer last5 and status email templates

Revision ID: 2c7b9f1e4a55
Revises: f3c8e2a1d5b6
Create Date: 2026-06-22 18:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2c7b9f1e4a55"
down_revision: Union[str, tuple[str, str], None] = "f3c8e2a1d5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("orders", "shipping_fee"):
        op.add_column("orders", sa.Column("shipping_fee", sa.Integer(), nullable=False, server_default="0"))
        op.alter_column("orders", "shipping_fee", server_default=None)

    if not _has_column("orders", "bank_transfer_last5"):
        op.add_column("orders", sa.Column("bank_transfer_last5", sa.String(length=5), nullable=True))

    if not _has_column("order_statuses", "customer_email_subject_template"):
        op.add_column("order_statuses", sa.Column("customer_email_subject_template", sa.String(length=255), nullable=True))

    if not _has_column("order_statuses", "customer_email_body_template"):
        op.add_column("order_statuses", sa.Column("customer_email_body_template", sa.Text(), nullable=True))

    if not _has_column("order_statuses", "admin_email_subject_template"):
        op.add_column("order_statuses", sa.Column("admin_email_subject_template", sa.String(length=255), nullable=True))

    if not _has_column("order_statuses", "admin_email_body_template"):
        op.add_column("order_statuses", sa.Column("admin_email_body_template", sa.Text(), nullable=True))


def downgrade() -> None:
    if _has_column("order_statuses", "admin_email_body_template"):
        op.drop_column("order_statuses", "admin_email_body_template")

    if _has_column("order_statuses", "admin_email_subject_template"):
        op.drop_column("order_statuses", "admin_email_subject_template")

    if _has_column("order_statuses", "customer_email_body_template"):
        op.drop_column("order_statuses", "customer_email_body_template")

    if _has_column("order_statuses", "customer_email_subject_template"):
        op.drop_column("order_statuses", "customer_email_subject_template")

    if _has_column("orders", "bank_transfer_last5"):
        op.drop_column("orders", "bank_transfer_last5")

    if _has_column("orders", "shipping_fee"):
        op.drop_column("orders", "shipping_fee")
