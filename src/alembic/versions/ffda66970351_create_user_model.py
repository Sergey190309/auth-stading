"""Create user model

Revision ID: ffda66970351
Revises: 6c48d9e68477
Create Date: 2025-11-13 11:04:12.523485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffda66970351'
down_revision: Union[str, Sequence[str], None] = '6c48d9e68477'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
