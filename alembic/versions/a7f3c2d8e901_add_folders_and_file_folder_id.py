"""add_folders_and_file_folder_id

Revision ID: a7f3c2d8e901
Revises: 11323c4f1556
Create Date: 2026-06-20 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a7f3c2d8e901'
down_revision: Union[str, None] = '11323c4f1556'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'subtopic_folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('subtopic_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('subtopics.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('subtopic_folders.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.add_column('subtopic_files', sa.Column(
        'folder_id',
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey('subtopic_folders.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    ))


def downgrade() -> None:
    op.drop_column('subtopic_files', 'folder_id')
    op.drop_table('subtopic_folders')
