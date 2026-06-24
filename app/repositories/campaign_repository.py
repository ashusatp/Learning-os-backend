import logging
from datetime import date
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaign import RevisionCampaign
from app.models.campaign_item import CampaignItem
from app.models.campaign_scope import CampaignScope
from app.models.enum import CampaignStatus

logger = logging.getLogger(__name__)


class CampaignRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Campaign CRUD ──

    async def create_campaign(self, campaign: RevisionCampaign):
        self.db.add(campaign)
        await self.db.flush()
        return campaign

    async def get_campaign_by_id(self, campaign_id: UUID):
        query = (
            select(RevisionCampaign)
            .options(selectinload(RevisionCampaign.scopes))
            .where(RevisionCampaign.id == campaign_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_campaigns_by_user(self, user_id: UUID, status: CampaignStatus | None = None):
        query = (
            select(RevisionCampaign)
            .where(RevisionCampaign.user_id == user_id)
        )
        if status:
            query = query.where(RevisionCampaign.status == status)
        query = query.order_by(RevisionCampaign.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_campaign(self, campaign: RevisionCampaign):
        await self.db.flush()
        return campaign

    async def delete_campaign(self, campaign: RevisionCampaign):
        await self.db.delete(campaign)
        await self.db.flush()

    # ── Scope ──

    async def create_scope(self, scope: CampaignScope):
        self.db.add(scope)
        await self.db.flush()
        return scope

    async def bulk_create_scopes(self, scopes: list[CampaignScope]):
        self.db.add_all(scopes)
        await self.db.flush()

    # ── Items ──

    async def bulk_create_items(self, items: list[CampaignItem]):
        self.db.add_all(items)
        await self.db.flush()

    async def get_item_by_id(self, item_id: UUID):
        query = select(CampaignItem).where(CampaignItem.id == item_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_items_for_date(self, campaign_id: UUID, target_date: date):
        query = (
            select(CampaignItem)
            .where(
                CampaignItem.campaign_id == campaign_id,
                CampaignItem.scheduled_date == target_date,
            )
            .order_by(CampaignItem.order_in_day.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_items_for_campaign(self, campaign_id: UUID):
        query = (
            select(CampaignItem)
            .where(CampaignItem.campaign_id == campaign_id)
            .order_by(CampaignItem.scheduled_date.asc(), CampaignItem.order_in_day.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_items(self, campaign_id: UUID):
        query = (
            select(func.count())
            .select_from(CampaignItem)
            .where(CampaignItem.campaign_id == campaign_id)
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def count_completed_items(self, campaign_id: UUID):
        query = (
            select(func.count())
            .select_from(CampaignItem)
            .where(
                CampaignItem.campaign_id == campaign_id,
                CampaignItem.is_completed == True,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def update_item(self, item: CampaignItem):
        await self.db.flush()
        return item

    # ── Today's queue across all active campaigns for a user ──

    async def get_incomplete_past_items(self, campaign_id: UUID, before_date: date):
        """Get incomplete items scheduled before the given date."""
        query = (
            select(CampaignItem)
            .where(
                CampaignItem.campaign_id == campaign_id,
                CampaignItem.scheduled_date < before_date,
                CampaignItem.is_completed == False,
            )
            .order_by(CampaignItem.scheduled_date.asc(), CampaignItem.order_in_day.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_max_order_for_date(self, campaign_id: UUID, target_date: date) -> int:
        query = (
            select(func.coalesce(func.max(CampaignItem.order_in_day), -1))
            .where(
                CampaignItem.campaign_id == campaign_id,
                CampaignItem.scheduled_date == target_date,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def get_todays_items_for_user(self, user_id: UUID, target_date: date):
        query = (
            select(CampaignItem, RevisionCampaign.name, RevisionCampaign.campaign_type)
            .join(RevisionCampaign, CampaignItem.campaign_id == RevisionCampaign.id)
            .where(
                RevisionCampaign.user_id == user_id,
                RevisionCampaign.status == CampaignStatus.ACTIVE,
                CampaignItem.scheduled_date == target_date,
            )
            .order_by(
                RevisionCampaign.id,
                CampaignItem.order_in_day.asc(),
            )
        )
        result = await self.db.execute(query)
        return result.all()
