"""add oauth fields to users

Revision ID: a3f2b8c9d1e4
Revises: c1b1cf4ff4a2
Create Date: 2026-06-18 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a3f2b8c9d1e4'
down_revision: Union[str, None] = 'c1b1cf4ff4a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('auth_provider', sa.String(), nullable=True))
    op.add_column('users', sa.Column('auth_provider_id', sa.String(), nullable=True))
    op.alter_column('users', 'password_hash', existing_type=sa.String(), nullable=True)

def downgrade() -> None:
    op.alter_column('users', 'password_hash', existing_type=sa.String(), nullable=False)
    op.drop_column('users', 'auth_provider_id')
    op.drop_column('users', 'auth_provider')
