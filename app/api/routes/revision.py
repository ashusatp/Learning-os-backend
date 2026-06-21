import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth_dependency import get_current_user
from app.api.dependencies.revision_dependency import get_revision_service
from app.models.user import User
from app.schema.pagination import PaginatedResponse
from app.schema.revision_schema import (
    CompleteRevisionRequest,
    RescheduleRevisionRequest,
    RevisionCompleteResponse,
    RevisionLogResponse,
    RevisionQueueResponse,
    RevisionScheduleResponse,
    RevisionStatsResponse,
    UpdateRevisionSettingsRequest,
    UserRevisionSettingsResponse,
)
from app.schema.subtopic_schema import SubTopicResponse
from app.services.revision_service import RevisionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Revisions"])


# ── Queue & Stats ──

@router.get(
    "/revisions/queue",
    response_model=RevisionQueueResponse,
)
async def get_global_revision_queue(
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    await service.check_and_reset_streak_global(user.id)

    queue = await service.get_global_queue(user.id)
    stats = await service.get_global_stats(user.id, queue=queue)
    return {**queue, "stats": stats}


@router.get(
    "/goals/{goal_id}/revisions/queue",
    response_model=RevisionQueueResponse,
)
async def get_revision_queue(
    goal_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    # Lazy streak check — reset if user missed yesterday
    await service.check_and_reset_streak(user.id, goal_id)

    queue = await service.get_queue(goal_id)
    stats = await service.get_stats(goal_id, user.id, queue=queue)
    return {**queue, "stats": stats}


@router.get(
    "/goals/{goal_id}/revisions/stats",
    response_model=RevisionStatsResponse,
)
async def get_revision_stats(
    goal_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.get_stats(goal_id, user.id)


# ── Schedule Management ──

@router.post(
    "/subtopics/{subtopic_id}/revision-schedule",
    response_model=RevisionScheduleResponse,
    status_code=201,
)
async def create_revision_schedule(
    subtopic_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.create_schedule(subtopic_id)


@router.get(
    "/subtopics/{subtopic_id}/revision-schedule",
    response_model=RevisionScheduleResponse,
)
async def get_revision_schedule(
    subtopic_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.get_schedule(subtopic_id)


# ── Revision Actions ──

@router.post(
    "/revisions/{schedule_id}/complete",
    response_model=RevisionCompleteResponse,
)
async def complete_revision(
    schedule_id: UUID,
    payload: CompleteRevisionRequest,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    schedule, log, promotion_suggestion, penalty_applied = await service.complete_revision(
        schedule_id,
        quality_rating=payload.quality_rating,
        user_id=user.id,
        revision_notes=payload.revision_notes,
    )
    return {
        "schedule": schedule,
        "log": log,
        "next_interval_days": schedule.current_interval_days,
        "new_ease_factor": schedule.ease_factor,
        "next_revision_at": schedule.next_revision_at,
        "promotion_suggestion": promotion_suggestion,
        "penalty_applied": penalty_applied,
    }


@router.post(
    "/revisions/{schedule_id}/skip",
    response_model=RevisionScheduleResponse,
)
async def skip_revision(
    schedule_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.skip_revision(schedule_id)


@router.post(
    "/revisions/{schedule_id}/reschedule",
    response_model=RevisionScheduleResponse,
)
async def reschedule_revision(
    schedule_id: UUID,
    payload: RescheduleRevisionRequest,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.reschedule_revision(schedule_id, payload.new_date)


@router.post(
    "/revisions/{schedule_id}/pause",
    response_model=RevisionScheduleResponse,
)
async def pause_revision(
    schedule_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.pause_schedule(schedule_id)


@router.post(
    "/revisions/{schedule_id}/resume",
    response_model=RevisionScheduleResponse,
)
async def resume_revision(
    schedule_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.resume_schedule(schedule_id)


# ── Revision Logs ──

@router.get(
    "/subtopics/{subtopic_id}/revision-logs",
    response_model=PaginatedResponse[RevisionLogResponse],
)
async def get_revision_logs(
    subtopic_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.get_logs(subtopic_id, page, page_size)


# ── User Revision Settings ──

@router.get(
    "/revision-settings",
    response_model=UserRevisionSettingsResponse,
)
async def get_revision_settings(
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.get_or_create_settings(user.id)


@router.patch(
    "/revision-settings",
    response_model=UserRevisionSettingsResponse,
)
async def update_revision_settings(
    payload: UpdateRevisionSettingsRequest,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    data = payload.model_dump(exclude_unset=True)
    return await service.update_settings(user.id, **data)


# ── Mastery Promotion ──

@router.post(
    "/subtopics/{subtopic_id}/promote-mastery",
    response_model=SubTopicResponse,
)
async def promote_mastery(
    subtopic_id: UUID,
    new_level: str = Query(..., description="Target mastery level"),
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    return await service.promote_mastery(subtopic_id, new_level)


# ── Cron / Admin endpoints ──

@router.post("/goals/{goal_id}/revisions/process-missed")
async def process_missed_revisions(
    goal_id: UUID,
    user: User = Depends(get_current_user),
    service: RevisionService = Depends(get_revision_service),
):
    count = await service.process_missed_revisions(goal_id)
    return {"processed": count}
