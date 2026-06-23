"""add site contents table

Revision ID: h7c1e2f9a4b3
Revises: 6b2a1c4d5e9f, g4d9e3b1c6a27
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "h7c1e2f9a4b3"
down_revision: Union[str, tuple[str, str], None] = ("6b2a1c4d5e9f", "g4d9e3b1c6a27")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_contents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_key", sa.String(length=80), nullable=False),
        sa.Column("content_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_contents_page_key", "site_contents", ["page_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_site_contents_page_key", table_name="site_contents")
    op.drop_table("site_contents")
