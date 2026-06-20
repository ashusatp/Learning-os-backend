"""add_accounts_table

Revision ID: b8e4f1a2c3d5
Revises: a7f3c2d8e901
Create Date: 2026-06-20 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b8e4f1a2c3d5'
down_revision: Union[str, None] = 'a7f3c2d8e901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  unique=True, nullable=False, index=True),
        sa.Column('ai_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ai_requests_today', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ai_requests_last_reset', sa.DateTime(timezone=True), nullable=True),
        sa.Column('plan', sa.String(), nullable=False, server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create an account row for every existing user
    op.execute("""
        INSERT INTO accounts (id, user_id, ai_enabled, ai_requests_today, plan, created_at, updated_at)
        SELECT gen_random_uuid(), id, false, 0, 'free', now(), now()
        FROM users
        WHERE id NOT IN (SELECT user_id FROM accounts)
    """)


def downgrade() -> None:
    op.drop_table('accounts')
