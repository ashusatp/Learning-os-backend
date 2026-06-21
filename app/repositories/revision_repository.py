import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import today_start_utc
from app.models.revision_schedule import RevisionSchedule
from app.models.revision_log import RevisionLog
from app.models.user_revision_settings import UserRevisionSettings
from app.models.subtopic import SubTopic
from app.models.topic import Topic
from app.models.subject import Subject
from app.models.goal import Goal
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
                SubTopic.topic_id,
                Topic.subject_id,
                Subject.goal_id,
                Goal.title.label("goal_title"),
            )
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Subject.goal_id == goal_id,
                Goal.is_archived == False,
                RevisionSchedule.is_active == True,
                RevisionSchedule.next_revision_at <= upcoming_cutoff,
            )
            .order_by(RevisionSchedule.next_revision_at.asc())
        )
        result = await self.db.execute(query)
        return result.all()

    async def get_queue_for_user(self, user_id: UUID, upcoming_days: int = 3):
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
                SubTopic.topic_id,
                Topic.subject_id,
                Subject.goal_id,
                Goal.title.label("goal_title"),
            )
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                Goal.is_archived == False,
                RevisionSchedule.is_active == True,
                RevisionSchedule.next_revision_at <= upcoming_cutoff,
            )
            .order_by(RevisionSchedule.next_revision_at.asc())
        )
        result = await self.db.execute(query)
        return result.all()

    async def count_completed_today_for_user(self, user_id: UUID):
        start_of_day = today_start_utc()

        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
                RevisionLog.completed_at >= start_of_day,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_completed_in_range_for_user(self, user_id: UUID, since: datetime):
        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
                RevisionLog.completed_at >= since,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_scheduled_in_range_for_user(self, user_id: UUID, since: datetime):
        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                RevisionLog.scheduled_for >= since,
                RevisionLog.event_type.in_([
                    RevisionEventType.COMPLETED,
                    RevisionEventType.MISSED,
                    RevisionEventType.SKIPPED,
                ]),
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def get_calendar_data_for_user(self, user_id: UUID, start: datetime, end: datetime):
        """Get completed and scheduled revision counts per day for a date range."""
        # Completed revisions grouped by date (in IST)
        ist_completed = func.timezone('Asia/Kolkata', RevisionLog.completed_at)
        completed_query = (
            select(
                func.date(ist_completed).label("day"),
                func.count().label("count"),
            )
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
                RevisionLog.completed_at >= start,
                RevisionLog.completed_at <= end,
            )
            .group_by(func.date(ist_completed))
        )
        completed_result = await self.db.execute(completed_query)
        completed = {str(row.day): row.count for row in completed_result.all()}

        # Scheduled (upcoming) revisions grouped by date (in IST)
        ist_scheduled = func.timezone('Asia/Kolkata', RevisionSchedule.next_revision_at)
        scheduled_query = (
            select(
                func.date(ist_scheduled).label("day"),
                func.count().label("count"),
            )
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                Goal.is_archived == False,
                RevisionSchedule.is_active == True,
                RevisionSchedule.next_revision_at >= start,
                RevisionSchedule.next_revision_at <= end,
            )
            .group_by(func.date(ist_scheduled))
        )
        scheduled_result = await self.db.execute(scheduled_query)
        scheduled = {str(row.day): row.count for row in scheduled_result.all()}

        return completed, scheduled

    async def get_items_for_date(self, user_id: UUID, date_start: datetime, date_end: datetime):
        """Get scheduled revisions for a specific date range, plus completed logs."""
        # Scheduled items whose next_revision_at falls on this date
        scheduled_query = (
            select(
                RevisionSchedule,
                SubTopic.name.label("subtopic_name"),
                SubTopic.mastery_level,
                SubTopic.mistake_count,
                SubTopic.exam_frequency,
                SubTopic.marks_per_question,
                Topic.name.label("topic_name"),
                Subject.name.label("subject_name"),
                SubTopic.topic_id,
                Topic.subject_id,
                Subject.goal_id,
                Goal.title.label("goal_title"),
            )
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                Goal.is_archived == False,
                RevisionSchedule.is_active == True,
                RevisionSchedule.next_revision_at >= date_start,
                RevisionSchedule.next_revision_at < date_end,
            )
            .order_by(RevisionSchedule.next_revision_at.asc())
        )
        result = await self.db.execute(scheduled_query)
        scheduled_rows = result.all()

        # Completed items on this date
        completed_query = (
            select(
                RevisionLog.subtopic_id,
                SubTopic.name.label("subtopic_name"),
                SubTopic.mastery_level,
                Topic.name.label("topic_name"),
                Subject.name.label("subject_name"),
                Subject.goal_id,
                Goal.title.label("goal_title"),
                RevisionLog.quality_rating,
                RevisionLog.completed_at,
            )
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
                RevisionLog.completed_at >= date_start,
                RevisionLog.completed_at < date_end,
            )
            .order_by(RevisionLog.completed_at.asc())
        )
        completed_result = await self.db.execute(completed_query)
        completed_rows = completed_result.all()

        return scheduled_rows, completed_rows

    async def count_overdue_before_for_user(self, user_id: UUID, before: datetime):
        query = (
            select(func.count())
            .select_from(RevisionSchedule)
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                Goal.is_archived == False,
                RevisionSchedule.is_active == True,
                RevisionSchedule.next_revision_at < before,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

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
        start_of_day = today_start_utc()

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
                RevisionLog.event_type.in_([
                    RevisionEventType.COMPLETED,
                    RevisionEventType.MISSED,
                    RevisionEventType.SKIPPED,
                ]),
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_completed_in_date_range(self, goal_id: UUID, start: datetime, end: datetime):
        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(
                Subject.goal_id == goal_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
                RevisionLog.completed_at >= start,
                RevisionLog.completed_at <= end,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_scheduled_in_date_range(self, goal_id: UUID, start: datetime, end: datetime):
        """Count revision logs that were scheduled in a date range."""
        query = (
            select(func.count())
            .select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(
                Subject.goal_id == goal_id,
                RevisionLog.scheduled_for >= start,
                RevisionLog.scheduled_for <= end,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_overdue_before(self, goal_id: UUID, before: datetime):
        """Count active schedules with next_revision_at before a given datetime."""
        query = (
            select(func.count())
            .select_from(RevisionSchedule)
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Subject.goal_id == goal_id,
                Goal.is_archived == False,
                RevisionSchedule.is_active == True,
                RevisionSchedule.next_revision_at < before,
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

    # ── Goal lookup ──

    async def get_goal_id_for_subtopic(self, subtopic_id: UUID):
        query = (
            select(Subject.goal_id)
            .join(Topic, Subject.id == Topic.subject_id)
            .join(SubTopic, Topic.id == SubTopic.topic_id)
            .where(SubTopic.id == subtopic_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

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

    async def get_profile_stats(self, user_id: UUID):
        """Aggregate profile stats across all goals for a user."""
        from app.models.enum import MasteryLevel as ML

        # Count goals
        goal_count = await self.db.execute(
            select(func.count()).select_from(Goal).where(Goal.user_id == user_id)
        )

        # Count subjects
        subject_count = await self.db.execute(
            select(func.count()).select_from(Subject)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(Goal.user_id == user_id)
        )

        # Count topics
        topic_count = await self.db.execute(
            select(func.count()).select_from(Topic)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(Goal.user_id == user_id)
        )

        # Count subtopics + mastery distribution
        subtopic_base = (
            select(SubTopic.mastery_level, func.count().label("cnt"))
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(Goal.user_id == user_id)
            .group_by(SubTopic.mastery_level)
        )
        mastery_result = await self.db.execute(subtopic_base)
        mastery_dist = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in mastery_result.all()}

        total_subtopics = sum(mastery_dist.values())

        # Total revisions completed (all time)
        total_revisions = await self.db.execute(
            select(func.count()).select_from(RevisionLog)
            .join(SubTopic, RevisionLog.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                RevisionLog.event_type == RevisionEventType.COMPLETED,
            )
        )

        # Active schedules count
        active_schedules = await self.db.execute(
            select(func.count()).select_from(RevisionSchedule)
            .join(SubTopic, RevisionSchedule.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(
                Goal.user_id == user_id,
                RevisionSchedule.is_active == True,
            )
        )

        # Average confidence across all subtopics
        avg_confidence = await self.db.execute(
            select(func.avg(SubTopic.confidence_level))
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Goal, Subject.goal_id == Goal.id)
            .where(Goal.user_id == user_id)
        )

        return {
            "goal_count": goal_count.scalar() or 0,
            "subject_count": subject_count.scalar() or 0,
            "topic_count": topic_count.scalar() or 0,
            "subtopic_count": total_subtopics,
            "mastery_distribution": mastery_dist,
            "total_revisions": total_revisions.scalar() or 0,
            "active_schedules": active_schedules.scalar() or 0,
            "avg_confidence": round((avg_confidence.scalar() or 0) * 100, 1),
        }

    # ── Bulk archive operations ──

    async def bulk_set_active_for_goal(self, goal_id: UUID, is_active: bool):
        """Pause or resume all revision schedules under a goal."""
        subtopic_ids_query = (
            select(SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(Subject.goal_id == goal_id)
        )
        stmt = (
            update(RevisionSchedule)
            .where(RevisionSchedule.subtopic_id.in_(subtopic_ids_query))
            .values(is_active=is_active)
        )
        await self.db.execute(stmt)
        await self.db.flush()
