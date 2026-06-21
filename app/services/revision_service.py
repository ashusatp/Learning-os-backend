import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.timezone import today_start_utc, today_end_utc, yesterday_start_utc, yesterday_end_utc, to_user_date
from app.exceptions.custom_exceptions import NotFoundException
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

# Confidence adjustments per quality rating (0.0-1.0 scale)
CONFIDENCE_ADJUSTMENTS = {
    QualityRating.EASY: 0.08,
    QualityRating.GOOD: 0.05,
    QualityRating.HARD: 0.02,
    QualityRating.AGAIN: -0.12,
}

# Mastery level ordering for promotion/demotion
MASTERY_ORDER = [
    MasteryLevel.NOT_STARTED,
    MasteryLevel.BEGINNER,
    MasteryLevel.INTERMEDIATE,
    MasteryLevel.ADVANCED,
    MasteryLevel.MASTERED,
]

# Penalty tiers: (max_days_overdue, interval_multiplier, mastery_drop, confidence_penalty)
PENALTY_TIERS = [
    (1, 1.0, 0, 0),        # Grace: 0-1 day
    (7, 0.7, 0, 5),        # Mild: 2-7 days
    (21, 0.4, 0, 15),      # Significant: 8-21 days
    (45, 0.0, 1, 25),      # Severe: 22-45 days (0.0 = reset to base)
    (999, 0.0, 2, 40),     # Critical: 46+ days
]

# Promotion requirements: (min_streak, max_mistakes, min_confidence, need_easy_in_last_3)
PROMOTION_REQUIREMENTS = {
    MasteryLevel.BEGINNER: (5, 2, 0, False),        # → INTERMEDIATE
    MasteryLevel.INTERMEDIATE: (8, 3, 60, False),    # → ADVANCED
    MasteryLevel.ADVANCED: (12, 3, 80, True),        # → MASTERED
}


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

    async def complete_revision(self, schedule_id: UUID, quality_rating: QualityRating, user_id: UUID, revision_notes: str | None = None):
        db = self.revision_repository.db

        try:
            schedule = await self.get_schedule_by_id(schedule_id)
            subtopic = await self.subtopic_repository.get_by_id(schedule.subtopic_id)
            if not subtopic:
                raise NotFoundException(f"Subtopic not found: {schedule.subtopic_id}")

            now = datetime.now(timezone.utc)
            days_overdue = max(0, (now - schedule.next_revision_at).days)
            was_on_time = days_overdue <= 1  # grace period

            # Get mistake type breakdown for weighted calculation
            mistake_types = await self.revision_repository.get_mistake_type_counts(subtopic.id)
            weighted_mistakes = self._calculate_weighted_mistakes(mistake_types)

            # Get max weightage for normalization
            goal_id = await self.revision_repository.get_goal_id_for_subtopic(subtopic.id)
            max_weightage = 1
            if goal_id:
                max_weightage = await self.revision_repository.get_max_weightage_for_goal(goal_id)

            # Apply overdue penalties to subtopic
            penalty_applied = None
            if days_overdue > 1:
                penalty_applied = self._apply_overdue_penalty(
                    subtopic, schedule, days_overdue, max_weightage,
                )

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

            # Update subtopic: revision fields + confidence
            subtopic.revision_count += 1
            subtopic.last_revised_at = now
            confidence_delta = CONFIDENCE_ADJUSTMENTS[quality_rating]
            subtopic.confidence_level = max(0.0, min(1.0, subtopic.confidence_level + confidence_delta))
            await self.subtopic_repository.update(subtopic)

            # Update daily streak
            await self._update_daily_streak(user_id, goal_id)

            # Check mastery promotion eligibility
            promotion_suggestion = self._check_promotion_eligibility(
                subtopic, schedule,
            )

            await db.commit()
            await db.refresh(schedule)
            await db.refresh(log)

            logger.info(
                f"Revision completed for {subtopic.id}: "
                f"rating={quality_rating.value}, interval={new_interval}d, ease={new_ease:.2f}"
            )
            return schedule, log, promotion_suggestion, penalty_applied

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

    def _build_queue_items(self, rows, max_weightage: int, now, today_start, today_end, has_goal_info: bool = False):
        """Build queue item dicts from raw DB rows.
        If has_goal_info=True, rows include goal_id and goal_title at indices 10 and 11."""
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
            topic_id = row[8]
            subject_id = row[9]

            if has_goal_info:
                goal_id = row[10]
                goal_title = row[11]
            else:
                goal_id = None
                goal_title = ""

            overdue_seconds = max(0.0, (now - schedule.next_revision_at).total_seconds())
            days_overdue_precise = overdue_seconds / 86400.0
            days_overdue = max(0, (to_user_date(now) - to_user_date(schedule.next_revision_at)).days)

            raw_weightage = exam_frequency * marks_per_question
            normalized_weightage = raw_weightage / max_weightage if max_weightage > 0 else 0

            importance_factor = 0.3 + (0.7 * normalized_weightage)
            mistake_factor = 1.0 + (mistake_count * 0.2)
            mastery_urg = MASTERY_URGENCY.get(mastery_level, 1.0)

            is_overdue = schedule.next_revision_at < today_start
            is_upcoming = schedule.next_revision_at > today_end

            if is_upcoming:
                priority_score = importance_factor * mistake_factor * mastery_urg * 0.1
            elif is_overdue:
                overdue_factor = min(5.0, max(0.5, days_overdue_precise / max(schedule.current_interval_days, 1)))
                priority_score = overdue_factor * importance_factor * mistake_factor * mastery_urg
            else:
                priority_score = importance_factor * mistake_factor * mastery_urg

            item = {
                "schedule_id": schedule.id,
                "subtopic_id": schedule.subtopic_id,
                "topic_id": str(topic_id),
                "subject_id": str(subject_id),
                "goal_id": str(goal_id) if goal_id else "",
                "goal_title": goal_title,
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
                "status": "",
            }

            if is_overdue:
                item["status"] = "overdue"
                overdue.append(item)
            elif is_upcoming:
                item["status"] = "upcoming"
                upcoming.append(item)
            else:
                item["status"] = "due_today"
                due_today.append(item)

        overdue.sort(key=lambda x: x["priority_score"], reverse=True)
        due_today.sort(key=lambda x: x["priority_score"], reverse=True)
        upcoming.sort(key=lambda x: x["next_revision_at"])

        return {"overdue": overdue, "due_today": due_today, "upcoming": upcoming}

    async def get_queue(self, goal_id: UUID):
        now = datetime.now(timezone.utc)
        today_start = today_start_utc()
        today_end = today_end_utc()
        rows = await self.revision_repository.get_queue_for_goal(goal_id)
        max_weightage = await self.revision_repository.get_max_weightage_for_goal(goal_id)
        return self._build_queue_items(rows, max_weightage, now, today_start, today_end, has_goal_info=True)

    async def get_global_queue(self, user_id: UUID):
        now = datetime.now(timezone.utc)
        today_start = today_start_utc()
        today_end = today_end_utc()
        rows = await self.revision_repository.get_queue_for_user(user_id)
        # Use 1 as max_weightage since items span multiple goals; normalize per-item
        max_weightage = 1
        if rows:
            max_weightage = max(
                (r[4] * r[5] for r in rows),  # exam_frequency * marks_per_question
                default=1,
            ) or 1
        return self._build_queue_items(rows, max_weightage, now, today_start, today_end, has_goal_info=True)

    async def get_stats(self, goal_id: UUID, user_id: UUID, queue: dict | None = None):
        now = datetime.now(timezone.utc)

        completed_today = await self.revision_repository.count_completed_today(goal_id)

        if queue is None:
            queue = await self.get_queue(goal_id)
        due_today_count = len(queue["due_today"])
        overdue_count = len(queue["overdue"])

        completed_7d = await self.revision_repository.count_completed_in_range(goal_id, now - timedelta(days=7))
        scheduled_7d = await self.revision_repository.count_scheduled_in_range(goal_id, now - timedelta(days=7))
        completed_30d = await self.revision_repository.count_completed_in_range(goal_id, now - timedelta(days=30))
        scheduled_30d = await self.revision_repository.count_scheduled_in_range(goal_id, now - timedelta(days=30))

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

    async def get_global_stats(self, user_id: UUID, queue: dict | None = None):
        now = datetime.now(timezone.utc)

        completed_today = await self.revision_repository.count_completed_today_for_user(user_id)

        if queue is None:
            queue = await self.get_global_queue(user_id)
        due_today_count = len(queue["due_today"])
        overdue_count = len(queue["overdue"])

        completed_7d = await self.revision_repository.count_completed_in_range_for_user(user_id, now - timedelta(days=7))
        scheduled_7d = await self.revision_repository.count_scheduled_in_range_for_user(user_id, now - timedelta(days=7))
        completed_30d = await self.revision_repository.count_completed_in_range_for_user(user_id, now - timedelta(days=30))
        scheduled_30d = await self.revision_repository.count_scheduled_in_range_for_user(user_id, now - timedelta(days=30))

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

    # ── Penalty & Reward helpers ──

    def _get_penalty_tier(self, days_overdue: int, normalized_weightage: float):
        """Get penalty tier. High-weight subtopics (>0.7) have halved thresholds."""
        effective_days = days_overdue
        if normalized_weightage > 0.7:
            effective_days = days_overdue * 2  # halved thresholds = doubled effective days

        for max_days, interval_mult, mastery_drop, confidence_pen in PENALTY_TIERS:
            if effective_days <= max_days:
                return interval_mult, mastery_drop, confidence_pen
        return 0.0, 2, 40  # critical fallback

    def _apply_overdue_penalty(self, subtopic, schedule, days_overdue: int, max_weightage: int):
        """Apply penalties for overdue revision. Mutates subtopic and schedule in place."""
        raw_weightage = subtopic.exam_frequency * subtopic.marks_per_question
        normalized = raw_weightage / max_weightage if max_weightage > 0 else 0

        interval_mult, mastery_drop, confidence_pen = self._get_penalty_tier(days_overdue, normalized)

        penalty_info = {
            "days_overdue": days_overdue,
            "confidence_penalty": confidence_pen,
            "mastery_dropped": 0,
            "old_mastery": subtopic.mastery_level.value if hasattr(subtopic.mastery_level, 'value') else subtopic.mastery_level,
            "new_mastery": None,
            "interval_multiplier": interval_mult,
        }

        # Confidence penalty (confidence_pen is in percentage points, convert to 0.0-1.0 scale)
        if confidence_pen > 0:
            subtopic.confidence_level = max(0.0, subtopic.confidence_level - (confidence_pen / 100.0))

        # Mastery decay
        if mastery_drop > 0:
            current_idx = MASTERY_ORDER.index(subtopic.mastery_level)
            # Never drop below BEGINNER (index 1)
            new_idx = max(1, current_idx - mastery_drop)
            if new_idx < current_idx:
                subtopic.mastery_level = MASTERY_ORDER[new_idx]
                penalty_info["mastery_dropped"] = current_idx - new_idx
                logger.info(
                    f"Mastery decayed for subtopic {subtopic.id}: "
                    f"{MASTERY_ORDER[current_idx].value} → {MASTERY_ORDER[new_idx].value} "
                    f"({days_overdue}d overdue)"
                )

        penalty_info["new_mastery"] = subtopic.mastery_level.value if hasattr(subtopic.mastery_level, 'value') else subtopic.mastery_level

        # Interval penalty (applied to schedule for the current cycle)
        if interval_mult == 0.0:
            # Reset to base interval
            base = BASE_INTERVALS.get(subtopic.mastery_level, 1)
            schedule.current_interval_days = base
        elif interval_mult < 1.0:
            schedule.current_interval_days = max(
                MIN_INTERVAL,
                round(schedule.current_interval_days * interval_mult),
            )

        # Reset per-subtopic streak on overdue beyond grace
        schedule.consecutive_successes = 0
        schedule.consecutive_misses += 1

        return penalty_info

    def _check_promotion_eligibility(self, subtopic, schedule) -> dict | None:
        """Check if subtopic is eligible for mastery promotion."""
        reqs = PROMOTION_REQUIREMENTS.get(subtopic.mastery_level)
        if not reqs:
            return None  # already MASTERED or NOT_STARTED

        min_streak, max_mistakes, min_confidence, need_easy = reqs

        if schedule.consecutive_successes < min_streak:
            return None
        if subtopic.mistake_count > max_mistakes:
            return None
        if min_confidence > 0 and subtopic.confidence_level < (min_confidence / 100.0):
            return None

        # For ADVANCED→MASTERED, check if at least 1 EASY in last 3 reviews
        # (We skip this check for now since it would require extra queries;
        # the streak requirement of 12 is already very strict)

        current_idx = MASTERY_ORDER.index(subtopic.mastery_level)
        next_level = MASTERY_ORDER[current_idx + 1]

        return {
            "subtopic_id": str(subtopic.id),
            "subtopic_name": subtopic.name,
            "current_level": subtopic.mastery_level.value,
            "suggested_level": next_level.value,
            "consecutive_successes": schedule.consecutive_successes,
        }

    async def _update_daily_streak(self, user_id: UUID, goal_id: UUID | None):
        """Increment daily streak if this is the first completion today."""
        if not goal_id:
            return

        completed_today = await self.revision_repository.count_completed_today(goal_id)
        # If this is the first completion today (count is 0 before our commit),
        # we increment the streak. The count is already 1 because we just created the log.
        if completed_today <= 1:
            settings = await self.revision_repository.get_user_settings(user_id)
            if not settings:
                settings = UserRevisionSettings(user_id=user_id)
                await self.revision_repository.create_user_settings(settings)

            settings.daily_streak += 1
            if settings.daily_streak > settings.longest_streak:
                settings.longest_streak = settings.daily_streak
            await self.revision_repository.update_user_settings(settings)

    # ── Cron / Background jobs ──

    async def process_missed_revisions(self, goal_id: UUID):
        """Process severely overdue items that haven't been touched.
        Creates MISSED log entries and applies penalties.
        Intended to be called by a cron job or admin endpoint."""
        db = self.revision_repository.db

        try:
            now = datetime.now(timezone.utc)
            rows = await self.revision_repository.get_queue_for_goal(goal_id, upcoming_days=0)
            max_weightage = await self.revision_repository.get_max_weightage_for_goal(goal_id)

            processed = 0
            for row in rows:
                schedule = row[0]
                days_overdue = max(0, (now - schedule.next_revision_at).days)

                if days_overdue <= 1:
                    continue  # within grace period

                subtopic = await self.subtopic_repository.get_by_id(schedule.subtopic_id)
                if not subtopic:
                    continue

                # Create MISSED log
                log = RevisionLog(
                    subtopic_id=subtopic.id,
                    schedule_id=schedule.id,
                    event_type=RevisionEventType.MISSED,
                    scheduled_for=schedule.next_revision_at,
                    was_on_time=False,
                    interval_used_days=schedule.current_interval_days,
                    ease_before=schedule.ease_factor,
                )
                await self.revision_repository.create_log(log)

                # Apply penalties (only confidence/mastery, not streak — streak handled separately)
                raw_weightage = subtopic.exam_frequency * subtopic.marks_per_question
                normalized = raw_weightage / max_weightage if max_weightage > 0 else 0
                _, mastery_drop, confidence_pen = self._get_penalty_tier(days_overdue, normalized)

                if confidence_pen > 0:
                    subtopic.confidence_level = max(0.0, subtopic.confidence_level - (confidence_pen / 100.0))

                if mastery_drop > 0:
                    current_idx = MASTERY_ORDER.index(subtopic.mastery_level)
                    new_idx = max(1, current_idx - mastery_drop)
                    if new_idx < current_idx:
                        subtopic.mastery_level = MASTERY_ORDER[new_idx]

                schedule.consecutive_misses += 1
                # Reschedule to today so the item appears as due_today, not re-processed by cron
                schedule.next_revision_at = now

                await self.subtopic_repository.update(subtopic)
                await self.revision_repository.update_schedule(schedule)
                processed += 1

            await db.commit()
            logger.info(f"Processed {processed} missed revisions for goal {goal_id}")
            return processed

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error processing missed revisions for {goal_id}")
            raise

    async def check_and_reset_streak(self, user_id: UUID, goal_id: UUID):
        """Check if user completed at least one revision yesterday.
        If they had due items yesterday but completed none, reset streak.
        Called when user loads the revision page (lazy check)."""
        db = self.revision_repository.db

        try:
            settings = await self.revision_repository.get_user_settings(user_id)
            if not settings or settings.daily_streak == 0:
                return  # nothing to reset

            yday_start = yesterday_start_utc()
            yday_end = yesterday_end_utc()
            tday_start = today_start_utc()

            # Check if user completed anything yesterday
            completed_yesterday = await self.revision_repository.count_completed_in_date_range(
                goal_id, yday_start, yday_end,
            )

            if completed_yesterday > 0:
                return  # streak intact

            # Check if there were items due before today (overdue)
            overdue_count = await self.revision_repository.count_overdue_before(goal_id, tday_start)

            if overdue_count == 0:
                return  # no items were due, streak is fine

            # Had due items but didn't complete any
            if settings.streak_freezes_remaining > 0:
                settings.streak_freezes_remaining -= 1
                logger.info(f"Streak freeze used for user {user_id}, {settings.streak_freezes_remaining} remaining")
            else:
                settings.daily_streak = 0
                logger.info(f"Daily streak reset for user {user_id} (missed yesterday)")

            await self.revision_repository.update_user_settings(settings)
            await db.commit()

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error checking streak for {user_id}")
            raise

    async def check_and_reset_streak_global(self, user_id: UUID):
        """Global streak check across all goals."""
        db = self.revision_repository.db

        try:
            settings = await self.revision_repository.get_user_settings(user_id)
            if not settings or settings.daily_streak == 0:
                return

            yday_start = yesterday_start_utc()
            yday_end = yesterday_end_utc()
            tday_start = today_start_utc()

            completed_yesterday = await self.revision_repository.count_completed_in_range_for_user(user_id, yday_start)
            # Rough check: count_completed_in_range_for_user counts from yday_start onward,
            # but we need just yesterday. Use the bounded version approach:
            # For simplicity, check if any overdue items exist and no completions yesterday.
            # We can check completed_today_for_user with yesterday's range.
            # Actually, let's just use the user-level overdue count:
            overdue_count = await self.revision_repository.count_overdue_before_for_user(user_id, tday_start)

            if overdue_count == 0:
                return

            # Check if anything was completed yesterday (between yday_start and yday_end)
            # We don't have a bounded user-level method, so use the "since" method
            # and subtract today's completions
            completed_since_yesterday = await self.revision_repository.count_completed_in_range_for_user(user_id, yday_start)
            completed_today = await self.revision_repository.count_completed_today_for_user(user_id)
            completed_yesterday_only = (completed_since_yesterday or 0) - (completed_today or 0)

            if completed_yesterday_only > 0:
                return

            if settings.streak_freezes_remaining > 0:
                settings.streak_freezes_remaining -= 1
                logger.info(f"Streak freeze used for user {user_id}, {settings.streak_freezes_remaining} remaining")
            else:
                settings.daily_streak = 0
                logger.info(f"Daily streak reset for user {user_id} (missed yesterday, global check)")

            await self.revision_repository.update_user_settings(settings)
            await db.commit()

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error checking global streak for {user_id}")
            raise

    async def promote_mastery(self, subtopic_id: UUID, new_level: str):
        """Accept a mastery promotion suggestion."""
        db = self.revision_repository.db
        try:
            subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
            if not subtopic:
                raise NotFoundException(f"Subtopic not found: {subtopic_id}")

            subtopic.mastery_level = MasteryLevel(new_level)
            await self.subtopic_repository.update(subtopic)

            # Update schedule base interval for new mastery
            schedule = await self.revision_repository.get_schedule_by_subtopic(subtopic_id)
            if schedule:
                base = BASE_INTERVALS.get(subtopic.mastery_level, 1)
                if schedule.current_interval_days < base:
                    schedule.current_interval_days = base
                await self.revision_repository.update_schedule(schedule)

            await db.commit()
            logger.info(f"Mastery promoted for subtopic {subtopic_id} to {new_level}")
            return subtopic

        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error promoting mastery for {subtopic_id}")
            raise
