"""add low stock threshold to products

Revision ID: j1a4f9d2c3b8
Revises: h7c1e2f9a4b3
Create Date: 2026-06-24 09:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "j1a4f9d2c3b8"
down_revision: Union[str, tuple[str, str], None] = "h7c1e2f9a4b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("low_stock_threshold", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_products_low_stock_threshold_non_negative",
        "products",
        "low_stock_threshold >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_products_low_stock_threshold_non_negative", "products", type_="check")
    op.drop_column("products", "low_stock_threshold")
