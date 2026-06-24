"""add_revision_campaigns_tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum types
campaign_type_enum = postgresql.ENUM(
    "SUBTOPIC_REVISION", "MISTAKE_REVIEW", "PYQ_PRACTICE",
    name="campaigntype",
    create_type=False,
)
campaign_scope_type_enum = postgresql.ENUM(
    "SUBJECT", "TOPIC",
    name="campaignscopetype",
    create_type=False,
)
campaign_status_enum = postgresql.ENUM(
    "ACTIVE", "PAUSED", "COMPLETED", "CANCELLED",
    name="campaignstatus",
    create_type=False,
)


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE campaigntype AS ENUM ('SUBTOPIC_REVISION', 'MISTAKE_REVIEW', 'PYQ_PRACTICE')")
    op.execute("CREATE TYPE campaignscopetype AS ENUM ('SUBJECT', 'TOPIC')")
    op.execute("CREATE TYPE campaignstatus AS ENUM ('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')")

    # revision_campaigns
    op.create_table(
        "revision_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("campaign_type", campaign_type_enum, nullable=False),
        sa.Column("status", campaign_status_enum, nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column("daily_frequency", sa.Integer(), nullable=False),
        sa.Column("parallel_subjects", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # campaign_scopes
    op.create_table(
        "campaign_scopes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("revision_campaigns.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("scope_type", campaign_scope_type_enum, nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # campaign_items
    op.create_table(
        "campaign_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("revision_campaigns.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subtopic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subtopics.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("mistake_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mistakes.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False, index=True),
        sa.Column("order_in_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("campaign_items")
    op.drop_table("campaign_scopes")
    op.drop_table("revision_campaigns")
    op.execute("DROP TYPE campaignstatus")
    op.execute("DROP TYPE campaignscopetype")
    op.execute("DROP TYPE campaigntype")
