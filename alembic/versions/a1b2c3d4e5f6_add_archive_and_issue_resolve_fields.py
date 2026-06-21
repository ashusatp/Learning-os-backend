"""add archive and issue resolve fields

Revision ID: a1b2c3d4e5f6
Revises: 53742b6c25fd
Create Date: 2026-06-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '53742b6c25fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('goals', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('subjects', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('topics', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('subtopics', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('issues', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('issues', 'resolved_at')
    op.drop_column('subtopics', 'is_archived')
    op.drop_column('topics', 'is_archived')
    op.drop_column('subjects', 'is_archived')
    op.drop_column('goals', 'is_archived')
