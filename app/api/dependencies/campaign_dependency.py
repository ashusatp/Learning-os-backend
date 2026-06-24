from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.campaign_engine_repository import CampaignEngineRepository
from app.services.campaign_service import CampaignService


def get_campaign_repository(
    db: AsyncSession = Depends(get_db),
):
    return CampaignRepository(db)


def get_campaign_engine_repository(
    db: AsyncSession = Depends(get_db),
):
    return CampaignEngineRepository(db)


def get_campaign_service(
    campaign_repo: CampaignRepository = Depends(get_campaign_repository),
    engine_repo: CampaignEngineRepository = Depends(get_campaign_engine_repository),
):
    return CampaignService(campaign_repo, engine_repo)
