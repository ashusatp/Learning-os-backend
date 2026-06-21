import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.revision_schedule import RevisionSchedule
from app.models.revision_log import RevisionLog
from app.models.user_revision_settings import UserRevisionSettings
from app.models.subtopic import SubTopic
from app.models.topic import Topic
from app.models.subject import Subject
from app.models.enum import RevisionEventType


logger = logging.getLogger(__name__)


class RevisionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Schedule CRUD ──

    async def get_schedule_by_id(self, schedule_id: UUID):
        query = select(RevisionSchedule).where(RevisionSchedule.id == schedule_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_schedule_by_subtopic(self, subtopic_id: UUID):
        query = select(RevisionSchedule).where(RevisionSchedule.subtopic_id == subtopic_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_schedule(self, schedule: RevisionSchedule):
        self.db.add(schedule)
        await self.db.flush()
        return schedule

    async def update_schedule(self, schedule: RevisionSchedule):
        await self.db.flush()
        return schedule

    async def delete_schedule(self, schedule: RevisionSchedule):
        await self.db.delete(schedule)
        await self.db.flush()

    # ── Queue: get all due/overdue/upcoming schedules for a user's goal ──

    async def get_queue_for_goal(self, goal_id: UUID, upcoming_days: int = 3):
        now = datetime.now(timezone.utc)
        upcoming_cutoff = now + timedelta(days=upcoming_days)

        query = (
            select(
                RevisionSchedule,
                SubTopic.name.label("subtopic_name"),
                SubTopic.mastery_level,
                SubTopic.mistake_count,
                SubTopic.exam_frequency,
                SubTopic.marks_per_question,
                Topic.name.label("topic_name"),
                Subject.name.label("subject_name"),
            )
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(
                Subject.goal_id == goal_id,
                RevisionSchedule.is_active == True,
                RevisionSchedule.next_revision_at <= upcoming_cutoff,
            )
            .order_by(RevisionSchedule.next_revision_at.asc())
        )
        result = await self.db.execute(query)
        return result.all()

    # ── Logs ──

    async def create_log(self, log: RevisionLog):
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_logs_by_subtopic(self, subtopic_id: UUID, limit: int, offset: int):
        base = select(RevisionLog).where(RevisionLog.subtopic_id == subtopic_id)

        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar()

        query = base.order_by(RevisionLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_logs_by_schedule(self, schedule_id: UUID):
        query = (
            select(RevisionLog)
            .where(RevisionLog.schedule_id == schedule_id)
            .order_by(RevisionLog.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_completed_today(self, goal_id: UUID):
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(
                Subject.goal_id == goal_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
                RevisionLog.completed_at >= start_of_day,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_completed_in_range(self, goal_id: UUID, since: datetime):
        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(
                Subject.goal_id == goal_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
                RevisionLog.completed_at >= since,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_scheduled_in_range(self, goal_id: UUID, since: datetime):
        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(
                Subject.goal_id == goal_id,
                RevisionLog.scheduled_for >= since,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    # ── User Revision Settings ──

    async def get_user_settings(self, user_id: UUID):
        query = select(UserRevisionSettings).where(UserRevisionSettings.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user_settings(self, settings: UserRevisionSettings):
        self.db.add(settings)
        await self.db.flush()
        return settings

    async def update_user_settings(self, settings: UserRevisionSettings):
        await self.db.flush()
        return settings

    # ── Weightage normalization ──

    async def get_max_weightage_for_goal(self, goal_id: UUID):
        query = (
            select(func.max(SubTopic.exam_frequency * SubTopic.marks_per_question))
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(Subject.goal_id == goal_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 1

    # ── Mistake type breakdown for a subtopic ──

    async def get_mistake_type_counts(self, subtopic_id: UUID):
        from app.models.mistake import Mistake
        query = (
            select(Mistake.mistake_type, func.count())
            .where(Mistake.subtopic_id == subtopic_id)
            .group_by(Mistake.mistake_type)
        )
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}
