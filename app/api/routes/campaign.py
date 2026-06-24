import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth_dependency import get_current_user
from app.api.dependencies.campaign_dependency import get_campaign_service
from app.models.enum import CampaignStatus
from app.models.user import User
from app.schema.campaign_schema import (
    CampaignCreateRequest,
    CampaignDetailResponse,
    CampaignItemCompleteRequest,
    CampaignItemResponse,
    CampaignPreviewRequest,
    CampaignPreviewResponse,
    CampaignQueueResponse,
    CampaignReorderRequest,
    CampaignResponse,
)
from app.services.campaign_service import CampaignService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# ── Preview (no DB write) ──

@router.post(
    "/preview",
    response_model=CampaignPreviewResponse,
)
async def preview_campaign(
    payload: CampaignPreviewRequest,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    data = payload.model_dump()
    data["scopes"] = [s.model_dump() for s in payload.scopes]
    if payload.subject_order:
        data["subject_order"] = [str(s) for s in payload.subject_order]
    return await service.preview(data)


# ── Create Campaign ──

@router.post(
    "",
    response_model=CampaignResponse,
    status_code=201,
)
async def create_campaign(
    payload: CampaignCreateRequest,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    data = payload.model_dump()
    data["scopes"] = [s.model_dump() for s in payload.scopes]
    if payload.subject_order:
        data["subject_order"] = [str(s) for s in payload.subject_order]
    campaign = await service.create_campaign(user.id, data)

    total = await service.campaign_repo.count_items(campaign.id)
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
        "completed_items": 0,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }


# ── List Campaigns ──

@router.get(
    "",
    response_model=list[CampaignResponse],
)
async def list_campaigns(
    status: CampaignStatus | None = Query(None),
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    return await service.get_campaigns(user.id, status)


# ── Today's Queue (all active campaigns) — must be before /{campaign_id} ──

@router.get(
    "/queue/today",
    response_model=list[CampaignQueueResponse],
)
async def get_todays_queue(
    target_date: date | None = Query(None),
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    return await service.get_todays_queue(user.id, target_date)


# ── Get Campaign Detail ──

@router.get(
    "/{campaign_id}",
    response_model=CampaignDetailResponse,
)
async def get_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    return await service.get_campaign(campaign_id, user.id)


# ── Get Campaign Items ──

@router.get(
    "/{campaign_id}/items",
    response_model=list[CampaignItemResponse],
)
async def get_campaign_items(
    campaign_id: UUID,
    target_date: date | None = Query(None),
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    return await service.get_campaign_items(campaign_id, user.id, target_date)


# ── Complete Item ──

@router.post(
    "/items/{item_id}/complete",
    response_model=CampaignItemResponse,
)
async def complete_item(
    item_id: UUID,
    payload: CampaignItemCompleteRequest = CampaignItemCompleteRequest(),
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    return await service.complete_item(item_id, user.id, payload.notes)


# ── Reorder Item ──

@router.post(
    "/{campaign_id}/reorder",
)
async def reorder_item(
    campaign_id: UUID,
    payload: CampaignReorderRequest,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    await service.reorder_item(campaign_id, user.id, payload.item_id, payload.target_date, payload.target_order)
    return {"ok": True}


# ── Pause / Resume / Cancel ──

@router.post(
    "/{campaign_id}/pause",
    response_model=CampaignResponse,
)
async def pause_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    campaign = await service.update_status(campaign_id, user.id, CampaignStatus.PAUSED)
    total = await service.campaign_repo.count_items(campaign.id)
    completed = await service.campaign_repo.count_completed_items(campaign.id)
    return {**_campaign_dict(campaign), "total_items": total, "completed_items": completed}


@router.post(
    "/{campaign_id}/resume",
    response_model=CampaignResponse,
)
async def resume_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    campaign = await service.update_status(campaign_id, user.id, CampaignStatus.ACTIVE)
    total = await service.campaign_repo.count_items(campaign.id)
    completed = await service.campaign_repo.count_completed_items(campaign.id)
    return {**_campaign_dict(campaign), "total_items": total, "completed_items": completed}


@router.post(
    "/{campaign_id}/cancel",
    response_model=CampaignResponse,
)
async def cancel_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    campaign = await service.update_status(campaign_id, user.id, CampaignStatus.CANCELLED)
    total = await service.campaign_repo.count_items(campaign.id)
    completed = await service.campaign_repo.count_completed_items(campaign.id)
    return {**_campaign_dict(campaign), "total_items": total, "completed_items": completed}


# ── Delete ──

@router.delete(
    "/{campaign_id}",
    status_code=204,
)
async def delete_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
):
    await service.delete_campaign(campaign_id, user.id)


def _campaign_dict(campaign) -> dict:
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
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }
