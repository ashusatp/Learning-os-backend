import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import BadRequestException, NotFoundException
from app.models.enum import MasteryLevel, MistakeType, QualityRating, RevisionEventType
from app.models.revision_log import RevisionLog
from app.models.revision_schedule import RevisionSchedule
from app.models.user_revision_settings import UserRevisionSettings
from app.repositories.revision_repository import RevisionRepository
from app.repositories.subtopic_repository import SubTopicRepository

logger = logging.getLogger(__name__)

# ── Constants ──

BASE_INTERVALS = {
    MasteryLevel.BEGINNER: 1,
    MasteryLevel.INTERMEDIATE: 2,
    MasteryLevel.ADVANCED: 4,
    MasteryLevel.MASTERED: 7,
}

MASTERY_URGENCY = {
    MasteryLevel.BEGINNER: 1.5,
    MasteryLevel.INTERMEDIATE: 1.0,
    MasteryLevel.ADVANCED: 0.7,
    MasteryLevel.MASTERED: 0.4,
}

MISTAKE_TYPE_WEIGHTS = {
    MistakeType.CONCEPTUAL: 1.5,
    MistakeType.CALCULATION: 1.0,
    MistakeType.MISREAD: 0.8,
    MistakeType.TIME_PRESSURE: 0.6,
    MistakeType.SILLY: 0.4,
    MistakeType.OTHER: 0.8,
}

MIN_INTERVAL = 1
MAX_INTERVAL = 180
MIN_EASE = 1.3
MAX_EASE = 3.5
DEFAULT_EASE = 2.5


class RevisionService:

    def __init__(
        self,
        revision_repository: RevisionRepository,
        subtopic_repository: SubTopicRepository,
    ):
        self.revision_repository = revision_repository
        self.subtopic_repository = subtopic_repository

    # ── Schedule creation ──

    async def create_schedule(self, subtopic_id: UUID):
        db = self.revision_repository.db

        try:
            subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
            if not subtopic:
                raise NotFoundException(f"Subtopic not found: {subtopic_id}")

            existing = await self.revision_repository.get_schedule_by_subtopic(subtopic_id)
            if existing:
                return existing

            mastery = subtopic.mastery_level or MasteryLevel.BEGINNER
            base = BASE_INTERVALS.get(mastery, 1)

            schedule = RevisionSchedule(
                subtopic_id=subtopic_id,
                next_revision_at=datetime.now(timezone.utc) + timedelta(days=base),
                current_interval_days=base,
                ease_factor=DEFAULT_EASE,
            )
            await self.revision_repository.create_schedule(schedule)
            await db.commit()
            await db.refresh(schedule)

            logger.info(f"Revision schedule created for subtopic {subtopic_id}, first review in {base}d")
            return schedule

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error creating revision schedule for {subtopic_id}")
            raise
        except Exception:
            await db.rollback()
            logger.exception(f"Error creating revision schedule for {subtopic_id}")
            raise

    # ── Get schedule ──

    async def get_schedule(self, subtopic_id: UUID):
        schedule = await self.revision_repository.get_schedule_by_subtopic(subtopic_id)
        if not schedule:
            raise NotFoundException(f"No revision schedule for subtopic: {subtopic_id}")
        return schedule

    async def get_schedule_by_id(self, schedule_id: UUID):
        schedule = await self.revision_repository.get_schedule_by_id(schedule_id)
        if not schedule:
            raise NotFoundException(f"Revision schedule not found: {schedule_id}")
        return schedule

    # ── Complete a revision ──

    async def complete_revision(self, schedule_id: UUID, quality_rating: QualityRating, revision_notes: str | None = None):
        db = self.revision_repository.db

        try:
            schedule = await self.get_schedule_by_id(schedule_id)
            subtopic = await self.subtopic_repository.get_by_id(schedule.subtopic_id)
            if not subtopic:
                raise NotFoundException(f"Subtopic not found: {schedule.subtopic_id}")

            now = datetime.now(timezone.utc)
            was_on_time = now <= schedule.next_revision_at + timedelta(days=1)  # grace period

            # Get mistake type breakdown for weighted calculation
            mistake_types = await self.revision_repository.get_mistake_type_counts(subtopic.id)
            weighted_mistakes = self._calculate_weighted_mistakes(mistake_types)

            # Get max weightage for normalization
            from app.models.topic import Topic
            from app.models.subject import Subject
            from sqlalchemy import select
            topic_result = await db.execute(
                select(Topic).where(Topic.id == subtopic.topic_id)
            )
            topic = topic_result.scalar_one_or_none()
            goal_id = None
            if topic:
                subject_result = await db.execute(
                    select(Subject).where(Subject.id == topic.subject_id)
                )
                subject = subject_result.scalar_one_or_none()
                goal_id = subject.goal_id if subject else None

            max_weightage = 1
            if goal_id:
                max_weightage = await self.revision_repository.get_max_weightage_for_goal(goal_id)

            # Calculate new interval and ease
            ease_before = schedule.ease_factor
            new_ease = self._calculate_new_ease(ease_before, quality_rating)
            new_interval = self._calculate_next_interval(
                schedule=schedule,
                quality_rating=quality_rating,
                ease_factor=new_ease,
                mastery_level=subtopic.mastery_level,
                weighted_mistakes=weighted_mistakes,
                subtopic_weightage=subtopic.exam_frequency * subtopic.marks_per_question,
                max_weightage=max_weightage,
            )

            # Create log entry
            log = RevisionLog(
                subtopic_id=subtopic.id,
                schedule_id=schedule.id,
                event_type=RevisionEventType.COMPLETED,
                quality_rating=quality_rating,
                scheduled_for=schedule.next_revision_at,
                completed_at=now,
                was_on_time=was_on_time,
                interval_used_days=schedule.current_interval_days,
                next_interval_days=new_interval,
                ease_before=ease_before,
                ease_after=new_ease,
                revision_notes=revision_notes,
            )
            await self.revision_repository.create_log(log)

            # Update schedule
            schedule.current_interval_days = new_interval
            schedule.ease_factor = new_ease
            schedule.next_revision_at = now + timedelta(days=new_interval)
            schedule.total_revisions += 1

            if quality_rating == QualityRating.AGAIN:
                schedule.consecutive_successes = 0
            else:
                schedule.consecutive_successes += 1

            schedule.consecutive_misses = 0

            await self.revision_repository.update_schedule(schedule)

            # Update subtopic revision fields
            subtopic.revision_count += 1
            subtopic.last_revised_at = now
            await self.subtopic_repository.update(subtopic)

            await db.commit()
            await db.refresh(schedule)
            await db.refresh(log)

            logger.info(
                f"Revision completed for {subtopic.id}: "
                f"rating={quality_rating.value}, interval={new_interval}d, ease={new_ease:.2f}"
            )
            return schedule, log

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error completing revision {schedule_id}")
            raise
        except Exception:
            await db.rollback()
            logger.exception(f"Error completing revision {schedule_id}")
            raise

    # ── Skip (snooze 1 day) ──

    async def skip_revision(self, schedule_id: UUID):
        db = self.revision_repository.db

        try:
            schedule = await self.get_schedule_by_id(schedule_id)
            now = datetime.now(timezone.utc)

            log = RevisionLog(
                subtopic_id=schedule.subtopic_id,
                schedule_id=schedule.id,
                event_type=RevisionEventType.SKIPPED,
                scheduled_for=schedule.next_revision_at,
                was_on_time=True,
                interval_used_days=schedule.current_interval_days,
                ease_before=schedule.ease_factor,
            )
            await self.revision_repository.create_log(log)

            schedule.next_revision_at = now + timedelta(days=1)
            await self.revision_repository.update_schedule(schedule)

            await db.commit()
            await db.refresh(schedule)

            logger.info(f"Revision skipped (snoozed 1d) for schedule {schedule_id}")
            return schedule

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error skipping revision {schedule_id}")
            raise
        except Exception:
            await db.rollback()
            logger.exception(f"Error skipping revision {schedule_id}")
            raise

    # ── Reschedule to specific date ──

    async def reschedule_revision(self, schedule_id: UUID, new_date: datetime):
        db = self.revision_repository.db

        try:
            schedule = await self.get_schedule_by_id(schedule_id)

            log = RevisionLog(
                subtopic_id=schedule.subtopic_id,
                schedule_id=schedule.id,
                event_type=RevisionEventType.RESCHEDULED,
                scheduled_for=schedule.next_revision_at,
                was_on_time=True,
                interval_used_days=schedule.current_interval_days,
                ease_before=schedule.ease_factor,
            )
            await self.revision_repository.create_log(log)

            schedule.next_revision_at = new_date
            await self.revision_repository.update_schedule(schedule)

            await db.commit()
            await db.refresh(schedule)

            logger.info(f"Revision rescheduled to {new_date} for schedule {schedule_id}")
            return schedule

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error rescheduling revision {schedule_id}")
            raise
        except Exception:
            await db.rollback()
            logger.exception(f"Error rescheduling revision {schedule_id}")
            raise

    # ── Pause / Resume ──

    async def pause_schedule(self, schedule_id: UUID):
        db = self.revision_repository.db
        try:
            schedule = await self.get_schedule_by_id(schedule_id)
            schedule.is_active = False
            await self.revision_repository.update_schedule(schedule)
            await db.commit()
            await db.refresh(schedule)
            logger.info(f"Revision schedule paused: {schedule_id}")
            return schedule
        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error pausing revision {schedule_id}")
            raise

    async def resume_schedule(self, schedule_id: UUID):
        db = self.revision_repository.db
        try:
            schedule = await self.get_schedule_by_id(schedule_id)
            schedule.is_active = True
            schedule.next_revision_at = datetime.now(timezone.utc) + timedelta(days=1)
            await self.revision_repository.update_schedule(schedule)
            await db.commit()
            await db.refresh(schedule)
            logger.info(f"Revision schedule resumed: {schedule_id}")
            return schedule
        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error resuming revision {schedule_id}")
            raise

    # ── Queue ──

    async def get_queue(self, goal_id: UUID):
        now = datetime.now(timezone.utc)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        rows = await self.revision_repository.get_queue_for_goal(goal_id)

        max_weightage = await self.revision_repository.get_max_weightage_for_goal(goal_id)

        overdue = []
        due_today = []
        upcoming = []

        for row in rows:
            schedule = row[0]
            subtopic_name = row[1]
            mastery_level = row[2]
            mistake_count = row[3]
            exam_frequency = row[4]
            marks_per_question = row[5]
            topic_name = row[6]
            subject_name = row[7]

            days_overdue = max(0, (now - schedule.next_revision_at).days)
            raw_weightage = exam_frequency * marks_per_question
            normalized_weightage = raw_weightage / max_weightage if max_weightage > 0 else 0

            # Priority score
            overdue_factor = min(5.0, max(0.0, days_overdue / max(schedule.current_interval_days, 1)))
            importance_factor = 0.3 + (0.7 * normalized_weightage)
            mistake_factor = 1.0 + (mistake_count * 0.2)
            mastery_urg = MASTERY_URGENCY.get(mastery_level, 1.0)

            priority_score = overdue_factor * importance_factor * mistake_factor * mastery_urg
            # For due-today items not yet overdue, give them a base priority
            if days_overdue == 0 and schedule.next_revision_at <= today_end:
                priority_score = importance_factor * mistake_factor * mastery_urg

            item = {
                "schedule_id": schedule.id,
                "subtopic_id": schedule.subtopic_id,
                "subtopic_name": subtopic_name,
                "topic_name": topic_name,
                "subject_name": subject_name,
                "mastery_level": mastery_level.value if hasattr(mastery_level, 'value') else mastery_level,
                "mistake_count": mistake_count,
                "exam_frequency": exam_frequency,
                "marks_per_question": marks_per_question,
                "next_revision_at": schedule.next_revision_at,
                "current_interval_days": schedule.current_interval_days,
                "ease_factor": schedule.ease_factor,
                "consecutive_successes": schedule.consecutive_successes,
                "days_overdue": days_overdue,
                "priority_score": round(priority_score, 3),
                "status": "overdue",
            }

            if schedule.next_revision_at < now.replace(hour=0, minute=0, second=0, microsecond=0):
                item["status"] = "overdue"
                overdue.append(item)
            elif schedule.next_revision_at <= today_end:
                item["status"] = "due_today"
                due_today.append(item)
            else:
                item["status"] = "upcoming"
                upcoming.append(item)

        # Sort by priority (highest first)
        overdue.sort(key=lambda x: x["priority_score"], reverse=True)
        due_today.sort(key=lambda x: x["priority_score"], reverse=True)
        upcoming.sort(key=lambda x: x["next_revision_at"])

        return {"overdue": overdue, "due_today": due_today, "upcoming": upcoming}

    async def get_stats(self, goal_id: UUID, user_id: UUID):
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        completed_today = await self.revision_repository.count_completed_today(goal_id)

        # Queue counts
        queue = await self.get_queue(goal_id)
        due_today_count = len(queue["due_today"])
        overdue_count = len(queue["overdue"])

        # Completion rates
        completed_7d = await self.revision_repository.count_completed_in_range(goal_id, now - timedelta(days=7))
        scheduled_7d = await self.revision_repository.count_scheduled_in_range(goal_id, now - timedelta(days=7))
        completed_30d = await self.revision_repository.count_completed_in_range(goal_id, now - timedelta(days=30))
        scheduled_30d = await self.revision_repository.count_scheduled_in_range(goal_id, now - timedelta(days=30))

        # User settings for streak
        settings = await self.revision_repository.get_user_settings(user_id)
        daily_streak = settings.daily_streak if settings else 0
        longest_streak = settings.longest_streak if settings else 0

        return {
            "due_today": due_today_count + overdue_count,
            "overdue_count": overdue_count,
            "completed_today": completed_today or 0,
            "daily_streak": daily_streak,
            "longest_streak": longest_streak,
            "completion_rate_7d": round(completed_7d / max(scheduled_7d, 1) * 100, 1),
            "completion_rate_30d": round(completed_30d / max(scheduled_30d, 1) * 100, 1),
        }

    # ── Logs ──

    async def get_logs(self, subtopic_id: UUID, page: int, page_size: int):
        offset = (page - 1) * page_size
        items, total = await self.revision_repository.get_logs_by_subtopic(subtopic_id, page_size, offset)
        total_pages = (total + page_size - 1) // page_size
        return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    # ── User Settings ──

    async def get_or_create_settings(self, user_id: UUID):
        db = self.revision_repository.db
        settings = await self.revision_repository.get_user_settings(user_id)
        if not settings:
            settings = UserRevisionSettings(user_id=user_id)
            await self.revision_repository.create_user_settings(settings)
            await db.commit()
            await db.refresh(settings)
        return settings

    async def update_settings(self, user_id: UUID, **kwargs):
        db = self.revision_repository.db
        try:
            settings = await self.get_or_create_settings(user_id)
            for key, value in kwargs.items():
                if value is not None:
                    setattr(settings, key, value)
            await self.revision_repository.update_user_settings(settings)
            await db.commit()
            await db.refresh(settings)
            logger.info(f"Revision settings updated for user {user_id}")
            return settings
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error updating revision settings for {user_id}")
            raise

    # ── Algorithm helpers ──

    def _calculate_new_ease(self, current_ease: float, rating: QualityRating) -> float:
        adjustments = {
            QualityRating.AGAIN: -0.20,
            QualityRating.HARD: -0.15,
            QualityRating.GOOD: 0.0,
            QualityRating.EASY: 0.15,
        }
        new_ease = current_ease + adjustments[rating]
        return max(MIN_EASE, min(MAX_EASE, new_ease))

    def _calculate_next_interval(
        self,
        schedule: RevisionSchedule,
        quality_rating: QualityRating,
        ease_factor: float,
        mastery_level,
        weighted_mistakes: float,
        subtopic_weightage: int,
        max_weightage: int,
    ) -> int:
        # Again → reset to 1 day
        if quality_rating == QualityRating.AGAIN:
            return MIN_INTERVAL

        revision_number = schedule.total_revisions + 1
        base = BASE_INTERVALS.get(mastery_level, 1)

        if revision_number == 1:
            interval = base
        elif revision_number == 2:
            interval = base * 2.5
        else:
            # Hard: smaller growth (1.2x), Good: ease_factor, Easy: ease_factor * 1.3
            if quality_rating == QualityRating.HARD:
                interval = schedule.current_interval_days * 1.2
            elif quality_rating == QualityRating.EASY:
                interval = schedule.current_interval_days * ease_factor * 1.3
            else:  # GOOD
                interval = schedule.current_interval_days * ease_factor

        # Weightage modifier: high-weight subtopics get shorter intervals
        if max_weightage > 0 and subtopic_weightage > 0:
            normalized = subtopic_weightage / max_weightage
            weightage_modifier = 1.0 - (0.3 * normalized)
            interval *= weightage_modifier

        # Mistake modifier
        mistake_modifier = max(0.4, 1.0 - (weighted_mistakes * 0.1))
        interval *= mistake_modifier

        # Streak bonus: +10% at 5, +20% at 10
        if schedule.consecutive_successes >= 10:
            interval *= 1.2
        elif schedule.consecutive_successes >= 5:
            interval *= 1.1

        return max(MIN_INTERVAL, min(MAX_INTERVAL, round(interval)))

    def _calculate_weighted_mistakes(self, mistake_types: dict) -> float:
        total = 0.0
        for mtype, count in mistake_types.items():
            weight = MISTAKE_TYPE_WEIGHTS.get(mtype, 0.8)
            total += weight * count
        return total
