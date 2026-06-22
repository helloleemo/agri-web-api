"""merge email verified and customer email heads

Revision ID: f2b9b6d5d123
Revises: e4a1c2d9f8b7, f2a9d1b4c6e7
Create Date: 2026-06-13 08:55:42.147493

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b9b6d5d123'
down_revision: Union[str, None] = ('e4a1c2d9f8b7', 'f2a9d1b4c6e7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
