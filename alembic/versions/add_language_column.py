"""add language column

Revision ID: add_language_column
Revises: 
Create Date: 2024-03-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_language_column'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('students', sa.Column('language', sa.String(), nullable=False, server_default='ru'))

def downgrade() -> None:
    op.drop_column('students', 'language') 