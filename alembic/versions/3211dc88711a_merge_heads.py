"""merge_heads

Revision ID: 3211dc88711a
Revises: add_language_column, b941e55aaf4c
Create Date: 2025-03-10 17:55:05.344712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3211dc88711a'
down_revision: Union[str, None] = ('add_language_column', 'b941e55aaf4c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
