import logging
import math
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import BadRequestException, NotFoundException
from app.models.campaign import RevisionCampaign
from app.models.campaign_item import CampaignItem
from app.models.campaign_scope import CampaignScope
from app.models.enum import CampaignScopeType, CampaignStatus, CampaignType
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.campaign_engine_repository import CampaignEngineRepository

logger = logging.getLogger(__name__)


class CampaignService:

    def __init__(
        self,
        campaign_repo: CampaignRepository,
        engine_repo: CampaignEngineRepository,
    ):
        self.campaign_repo = campaign_repo
        self.engine_repo = engine_repo

    # ── Preview (no DB write) ──

    async def preview(self, data: dict) -> dict:
        scopes = data["scopes"]
        subject_ids, topic_ids = self._extract_scope_ids(scopes)
        campaign_type = data["campaign_type"]
        total_days = data["total_days"]
        parallel = data.get("parallel_subjects", 1)
        daily_freq = data.get("daily_frequency")
        start = data["start_date"]
        subject_order = data.get("subject_order")

        grouped = await self._resolve_grouped(campaign_type, subject_ids, topic_ids)
        if not grouped:
            raise BadRequestException("No items found for the selected scope")

        # Reorder subjects if user specified
        if subject_order:
            order_map = {str(sid): i for i, sid in enumerate(subject_order)}
            grouped.sort(key=lambda g: order_map.get(g["subject_id"], 999))

        # Flatten with interleaving
        flat_items = self._interleave(grouped, parallel)
        total_items = len(flat_items)

        # Compute daily_frequency if not provided
        if not daily_freq:
            daily_freq = max(1, math.ceil(total_items / total_days))

        schedule = self._build_schedule(flat_items, start, total_days, daily_freq)
        actual_days = len(schedule)

        subjects_summary = [
            {
                "subject_id": g["subject_id"],
                "subject_name": g["subject_name"],
                "subtopic_count": len(g["subtopics"]),
            }
            for g in grouped
        ]

        return {
            "total_items": total_items,
            "total_days": actual_days,
            "daily_frequency": daily_freq,
            "parallel_subjects": parallel,
            "subjects": subjects_summary,
            "schedule": schedule,
        }

    # ── Create Campaign ──

    async def create_campaign(self, user_id: UUID, data: dict) -> RevisionCampaign:
        try:
            scopes_data = data["scopes"]
            subject_ids, topic_ids = self._extract_scope_ids(scopes_data)
            campaign_type = data["campaign_type"]
            total_days = data["total_days"]
            parallel = data.get("parallel_subjects", 1)
            daily_freq = data.get("daily_frequency")
            start = data["start_date"]
            subject_order = data.get("subject_order")

            grouped = await self._resolve_grouped(campaign_type, subject_ids, topic_ids)
            if not grouped:
                raise BadRequestException("No items found for the selected scope")

            if subject_order:
                order_map = {str(sid): i for i, sid in enumerate(subject_order)}
                grouped.sort(key=lambda g: order_map.get(g["subject_id"], 999))

            flat_items = self._interleave(grouped, parallel)
            total_items = len(flat_items)

            if not daily_freq:
                daily_freq = max(1, math.ceil(total_items / total_days))

            schedule = self._build_schedule(flat_items, start, total_days, daily_freq)
            actual_days = len(schedule)
            end = start + timedelta(days=actual_days - 1)

            campaign = RevisionCampaign(
                user_id=user_id,
                name=data["name"],
                campaign_type=campaign_type,
                status=CampaignStatus.ACTIVE,
                total_days=actual_days,
                daily_frequency=daily_freq,
                parallel_subjects=parallel,
                start_date=start,
                end_date=end,
            )
            campaign = await self.campaign_repo.create_campaign(campaign)

            # Create scopes
            db_scopes = []
            for sd in scopes_data:
                scope = CampaignScope(
                    campaign_id=campaign.id,
                    scope_type=sd["scope_type"],
                    subject_id=sd["subject_id"],
                    topic_id=sd.get("topic_id"),
                )
                db_scopes.append(scope)
            await self.campaign_repo.bulk_create_scopes(db_scopes)

            # Create items from schedule
            db_items = []
            for day in schedule:
                for item_data in day["items"]:
                    ci = CampaignItem(
                        campaign_id=campaign.id,
                        subtopic_id=item_data.get("subtopic_id"),
                        mistake_id=item_data.get("mistake_id"),
                        question_id=item_data.get("question_id"),
                        scheduled_date=day["date"],
                        order_in_day=item_data.get("order", 0),
                    )
                    db_items.append(ci)
            await self.campaign_repo.bulk_create_items(db_items)

            await self.campaign_repo.db.commit()
            logger.info(f"Created campaign '{campaign.name}' with {len(db_items)} items")
            return campaign

        except (BadRequestException,):
            await self.campaign_repo.db.rollback()
            raise
        except SQLAlchemyError as e:
            await self.campaign_repo.db.rollback()
            logger.error(f"Failed to create campaign: {e}")
            raise

    # ── Engine internals ──

    def _extract_scope_ids(self, scopes: list[dict]) -> tuple[list, list]:
        subject_ids = []
        topic_ids = []
        for s in scopes:
            scope_type = s.get("scope_type")
            if isinstance(scope_type, CampaignScopeType):
                scope_type = scope_type.value
            if scope_type == "SUBJECT":
                subject_ids.append(s["subject_id"])
            else:
                topic_ids.append(s["topic_id"])
        return subject_ids, topic_ids

    async def _resolve_grouped(self, campaign_type, subject_ids, topic_ids):
        if campaign_type == CampaignType.SUBTOPIC_REVISION or campaign_type == "SUBTOPIC_REVISION":
            return await self.engine_repo.get_subtopics_for_scope_grouped(
                subject_ids, topic_ids
            )
        # For mistakes/PYQs, wrap flat results into a single group
        if campaign_type == CampaignType.MISTAKE_REVIEW or campaign_type == "MISTAKE_REVIEW":
            flat = await self.engine_repo.get_mistakes_for_scope(subject_ids, topic_ids)
            if flat:
                return [{"subject_id": "mistakes", "subject_name": "Mistakes", "subtopics": flat}]
        if campaign_type == CampaignType.PYQ_PRACTICE or campaign_type == "PYQ_PRACTICE":
            flat = await self.engine_repo.get_pyqs_for_scope(subject_ids, topic_ids)
            if flat:
                return [{"subject_id": "pyqs", "subject_name": "PYQs", "subtopics": flat}]
        return []

    def _interleave(self, grouped: list[dict], parallel: int) -> list[dict]:
        """
        Interleave subtopics from `parallel` subjects at a time.
        E.g. parallel=2, subjects=[A(3 items), B(2 items), C(4 items)]:
        → A1, B1, A2, B2, A3, C1, C2, C3, C4
        When one subject finishes, the next one fills its slot.
        """
        # Build queues per subject
        queues = []
        for g in grouped:
            items = []
            for st in g["subtopics"]:
                item = {**st, "subject_name": g["subject_name"]}
                items.append(item)
            queues.append(items)

        result = []
        # Active slots: indices into `queues`
        remaining = list(range(len(queues)))
        active = remaining[:parallel]
        waiting = remaining[parallel:]
        # Cursor per active queue
        cursors = {i: 0 for i in active}

        while active:
            next_active = []
            for idx in active:
                q = queues[idx]
                c = cursors[idx]
                if c < len(q):
                    result.append(q[c])
                    cursors[idx] = c + 1
                    if cursors[idx] < len(q):
                        next_active.append(idx)
                    else:
                        # This subject is done, pull next from waiting
                        if waiting:
                            new_idx = waiting.pop(0)
                            cursors[new_idx] = 0
                            next_active.append(new_idx)
            active = next_active

        return result

    def _build_schedule(
        self, flat_items: list[dict], start: date, max_days: int, daily_freq: int
    ) -> list[dict]:
        schedule = []
        day_num = 0
        idx = 0

        while idx < len(flat_items) and day_num < max_days:
            day_items = []
            for order in range(daily_freq):
                if idx >= len(flat_items):
                    break
                item = flat_items[idx]
                day_items.append({**item, "order": order})
                idx += 1

            if day_items:
                schedule.append({
                    "date": start + timedelta(days=day_num),
                    "day_number": day_num + 1,
                    "items": day_items,
                })
            day_num += 1

        # If items remain (more items than max_days * daily_freq), extend
        while idx < len(flat_items):
            day_items = []
            for order in range(daily_freq):
                if idx >= len(flat_items):
                    break
                item = flat_items[idx]
                day_items.append({**item, "order": order})
                idx += 1
            if day_items:
                schedule.append({
                    "date": start + timedelta(days=day_num),
                    "day_number": day_num + 1,
                    "items": day_items,
                })
            day_num += 1

        return schedule

    # ── Reorder item ──

    async def reorder_item(self, campaign_id: UUID, user_id: UUID, item_id: UUID, target_date: date, target_order: int):
        try:
            campaign = await self.campaign_repo.get_campaign_by_id(campaign_id)
            if not campaign or campaign.user_id != user_id:
                raise NotFoundException("Campaign not found")

            item = await self.campaign_repo.get_item_by_id(item_id)
            if not item or item.campaign_id != campaign.id:
                raise NotFoundException("Item not found")

            old_date = item.scheduled_date
            old_order = item.order_in_day

            # Get items on target date to make room
            target_items = await self.campaign_repo.get_items_for_date(campaign_id, target_date)

            # Remove item from old position
            old_items = await self.campaign_repo.get_items_for_date(campaign_id, old_date)
            for oi in old_items:
                if oi.id != item.id and oi.order_in_day > old_order:
                    oi.order_in_day -= 1

            # Shift target items to make room
            for ti in target_items:
                if ti.order_in_day >= target_order and ti.id != item.id:
                    ti.order_in_day += 1

            item.scheduled_date = target_date
            item.order_in_day = target_order

            await self.campaign_repo.db.flush()
            await self.campaign_repo.db.commit()
            return item

        except NotFoundException:
            await self.campaign_repo.db.rollback()
            raise
        except SQLAlchemyError as e:
            await self.campaign_repo.db.rollback()
            logger.error(f"Failed to reorder item: {e}")
            raise

    # ── List Campaigns ──

    async def get_campaigns(self, user_id: UUID, status: CampaignStatus | None = None):
        campaigns = await self.campaign_repo.get_campaigns_by_user(user_id, status)
        result = []
        for c in campaigns:
            total = await self.campaign_repo.count_items(c.id)
            completed = await self.campaign_repo.count_completed_items(c.id)
            result.append({
                "id": c.id,
                "user_id": c.user_id,
                "name": c.name,
                "campaign_type": c.campaign_type,
                "status": c.status,
                "total_days": c.total_days,
                "daily_frequency": c.daily_frequency,
                "parallel_subjects": c.parallel_subjects,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "total_items": total,
                "completed_items": completed,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            })
        return result

    # ── Get Campaign Detail ──

    async def get_campaign(self, campaign_id: UUID, user_id: UUID):
        campaign = await self.campaign_repo.get_campaign_by_id(campaign_id)
        if not campaign or campaign.user_id != user_id:
            raise NotFoundException("Campaign not found")

        total = await self.campaign_repo.count_items(campaign.id)
        completed = await self.campaign_repo.count_completed_items(campaign.id)

        scope_responses = []
        for scope in campaign.scopes:
            names = await self.engine_repo.get_scope_names(scope.subject_id, scope.topic_id)
            scope_responses.append({
                "id": scope.id,
                "scope_type": scope.scope_type,
                "subject_id": scope.subject_id,
                "topic_id": scope.topic_id,
                "subject_name": names.get("subject_name"),
                "topic_name": names.get("topic_name"),
            })

        return {
            "id": campaign.id,
            "user_id": campaign.user_id,
            "name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "status": campaign.status,
            "total_days": campaign.total_days,
            "daily_frequency": campaign.daily_frequency,
            "parallel_subjects": campaign.parallel_subjects,
            "start_date": campaign.start_date,
            "end_date": campaign.end_date,
            "total_items": total,
            "completed_items": completed,
            "created_at": campaign.created_at,
            "updated_at": campaign.updated_at,
            "scopes": scope_responses,
        }

    # ── Carry over incomplete items ──

    async def _carry_over_incomplete(self, campaign_id: UUID, today: date):
        """Move incomplete items from past days to today."""
        past_items = await self.campaign_repo.get_incomplete_past_items(campaign_id, today)
        if not past_items:
            return 0

        max_order = await self.campaign_repo.get_max_order_for_date(campaign_id, today)
        next_order = max_order + 1

        for item in past_items:
            item.scheduled_date = today
            item.order_in_day = next_order
            next_order += 1

        await self.campaign_repo.db.flush()
        logger.info(f"Carried over {len(past_items)} items to {today} for campaign {campaign_id}")
        return len(past_items)

    # ── Today's Queue ──

    async def get_todays_queue(self, user_id: UUID, target_date: date | None = None):
        if target_date is None:
            target_date = date.today()

        # Auto carry-over for all active campaigns
        active_campaigns = await self.campaign_repo.get_campaigns_by_user(
            user_id, CampaignStatus.ACTIVE
        )
        for c in active_campaigns:
            carried = await self._carry_over_incomplete(c.id, target_date)
            if carried > 0:
                await self.campaign_repo.db.commit()

        rows = await self.campaign_repo.get_todays_items_for_user(user_id, target_date)

        campaigns_map: dict[UUID, dict] = {}
        for item, campaign_name, campaign_type in rows:
            if item.campaign_id not in campaigns_map:
                campaigns_map[item.campaign_id] = {
                    "campaign_id": item.campaign_id,
                    "campaign_name": campaign_name,
                    "campaign_type": campaign_type,
                    "scheduled_date": target_date,
                    "items": [],
                    "total_for_day": 0,
                    "completed_for_day": 0,
                }

            entry = campaigns_map[item.campaign_id]
            entry["total_for_day"] += 1
            if item.is_completed:
                entry["completed_for_day"] += 1

            item_data = await self._enrich_item(item)
            entry["items"].append(item_data)

        return list(campaigns_map.values())

    async def _enrich_item(self, item: CampaignItem) -> dict:
        names = await self.engine_repo.get_item_names(
            subtopic_id=item.subtopic_id,
            mistake_id=item.mistake_id,
            question_id=item.question_id,
        )
        return {
            "id": item.id,
            "campaign_id": item.campaign_id,
            "subtopic_id": item.subtopic_id,
            "mistake_id": item.mistake_id,
            "question_id": item.question_id,
            "scheduled_date": item.scheduled_date,
            "order_in_day": item.order_in_day,
            "is_completed": item.is_completed,
            "completed_at": item.completed_at,
            "notes": item.notes,
            **names,
        }

    # ── Complete Item ──

    async def complete_item(self, item_id: UUID, user_id: UUID, notes: str | None = None):
        try:
            item = await self.campaign_repo.get_item_by_id(item_id)
            if not item:
                raise NotFoundException("Campaign item not found")

            campaign = await self.campaign_repo.get_campaign_by_id(item.campaign_id)
            if not campaign or campaign.user_id != user_id:
                raise NotFoundException("Campaign item not found")

            if item.is_completed:
                raise BadRequestException("Item already completed")

            item.is_completed = True
            item.completed_at = datetime.now(timezone.utc)
            if notes:
                item.notes = notes

            await self.campaign_repo.update_item(item)

            total = await self.campaign_repo.count_items(campaign.id)
            completed = await self.campaign_repo.count_completed_items(campaign.id)
            if completed >= total:
                campaign.status = CampaignStatus.COMPLETED
                await self.campaign_repo.update_campaign(campaign)

            await self.campaign_repo.db.commit()
            return await self._enrich_item(item)

        except (NotFoundException, BadRequestException):
            await self.campaign_repo.db.rollback()
            raise
        except SQLAlchemyError as e:
            await self.campaign_repo.db.rollback()
            logger.error(f"Failed to complete campaign item: {e}")
            raise

    # ── Pause / Resume / Cancel ──

    async def update_status(self, campaign_id: UUID, user_id: UUID, new_status: CampaignStatus):
        try:
            campaign = await self.campaign_repo.get_campaign_by_id(campaign_id)
            if not campaign or campaign.user_id != user_id:
                raise NotFoundException("Campaign not found")

            campaign.status = new_status
            await self.campaign_repo.update_campaign(campaign)
            await self.campaign_repo.db.commit()
            return campaign

        except NotFoundException:
            await self.campaign_repo.db.rollback()
            raise
        except SQLAlchemyError as e:
            await self.campaign_repo.db.rollback()
            logger.error(f"Failed to update campaign status: {e}")
            raise

    # ── Delete Campaign ──

    async def delete_campaign(self, campaign_id: UUID, user_id: UUID):
        try:
            campaign = await self.campaign_repo.get_campaign_by_id(campaign_id)
            if not campaign or campaign.user_id != user_id:
                raise NotFoundException("Campaign not found")

            await self.campaign_repo.delete_campaign(campaign)
            await self.campaign_repo.db.commit()

        except NotFoundException:
            await self.campaign_repo.db.rollback()
            raise
        except SQLAlchemyError as e:
            await self.campaign_repo.db.rollback()
            logger.error(f"Failed to delete campaign: {e}")
            raise

    # ── Get items for a specific date ──

    async def get_campaign_items(self, campaign_id: UUID, user_id: UUID, target_date: date | None = None):
        campaign = await self.campaign_repo.get_campaign_by_id(campaign_id)
        if not campaign or campaign.user_id != user_id:
            raise NotFoundException("Campaign not found")

        # Auto carry-over incomplete past items to today
        if campaign.status == CampaignStatus.ACTIVE:
            today = date.today()
            carried = await self._carry_over_incomplete(campaign_id, today)
            if carried > 0:
                await self.campaign_repo.db.commit()

        if target_date:
            items = await self.campaign_repo.get_items_for_date(campaign_id, target_date)
        else:
            items = await self.campaign_repo.get_items_for_campaign(campaign_id)

        result = []
        for item in items:
            item_data = await self._enrich_item(item)
            result.append(item_data)
        return result
