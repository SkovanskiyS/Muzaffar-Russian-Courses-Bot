"""add_course_models

Revision ID: bd98cb64145a
Revises: 3211dc88711a
Create Date: 2025-03-10 17:55:25.199515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bd98cb64145a'
down_revision: Union[str, None] = '3211dc88711a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first
    difficulty_level = postgresql.ENUM('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT', name='difficultylevel')
    difficulty_level.create(op.get_bind())
    
    # Add column using the created enum type
    op.add_column('courses', sa.Column('difficulty_level', sa.Enum('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT', name='difficultylevel'), nullable=False, server_default='BEGINNER'))
    op.alter_column('courses', 'order_index',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade() -> None:
    # Drop the column first
    op.alter_column('courses', 'order_index',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('courses', 'difficulty_level')
    
    # Then drop the enum type
    difficulty_level = postgresql.ENUM('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT', name='difficultylevel')
    difficulty_level.drop(op.get_bind())
