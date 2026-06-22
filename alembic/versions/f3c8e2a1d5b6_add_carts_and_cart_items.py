"""add carts and cart_items

Revision ID: f3c8e2a1d5b6
Revises: 1f6a9c2d4b31
Create Date: 2026-06-22 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f3c8e2a1d5b6'
down_revision = '1f6a9c2d4b31'
branch_labels = None
depends_on = None


def upgrade():
    # Create carts table
    op.create_table(
        'carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('idx_carts_user_id', 'carts', ['user_id'], unique=False)

    # Create cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.CheckConstraint('quantity >= 1', name='ck_cart_items_quantity_positive'),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_cart_items_cart_id', 'cart_items', ['cart_id'], unique=False)


def downgrade():
    # Drop cart_items table
    op.drop_index('idx_cart_items_cart_id', table_name='cart_items')
    op.drop_table('cart_items')

    # Drop carts table
    op.drop_index('idx_carts_user_id', table_name='carts')
    op.drop_table('carts')
