import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.mistake_dependency import get_mistake_service
from app.schema.mistake_schema import (
    CreateMistakeRequest,
    UpdateMistakeRequest,
    MistakeResponse,
)
from app.services.mistake_service import MistakeService

logger = logging.getLogger(__name__)

# ── Subtopic-scoped routes ──

subtopic_router = APIRouter(
    prefix="/subtopics/{subtopic_id}/mistakes",
    tags=["Mistakes"],
)


@subtopic_router.post("", response_model=MistakeResponse, status_code=201)
async def create_mistake(
    subtopic_id: UUID,
    payload: CreateMistakeRequest,
    service: MistakeService = Depends(get_mistake_service),
):
    data = payload.model_dump(exclude={"subtopic_id"})
    return await service.create_mistake(subtopic_id=subtopic_id, **data)


@subtopic_router.get("", response_model=list[MistakeResponse])
async def get_mistakes(
    subtopic_id: UUID,
    resolved: bool | None = Query(None),
    service: MistakeService = Depends(get_mistake_service),
):
    return await service.get_mistakes_by_subtopic(subtopic_id, resolved)


@subtopic_router.get("/{mistake_id}", response_model=MistakeResponse)
async def get_mistake(
    subtopic_id: UUID,
    mistake_id: UUID,
    service: MistakeService = Depends(get_mistake_service),
):
    return await service.get_mistake(mistake_id)


@subtopic_router.put("/{mistake_id}", response_model=MistakeResponse)
async def update_mistake(
    subtopic_id: UUID,
    mistake_id: UUID,
    payload: UpdateMistakeRequest,
    service: MistakeService = Depends(get_mistake_service),
):
    data = payload.model_dump(exclude_unset=True)
    return await service.update_mistake(mistake_id, **data)


@subtopic_router.patch("/{mistake_id}/resolve", response_model=MistakeResponse)
async def resolve_mistake(
    subtopic_id: UUID,
    mistake_id: UUID,
    service: MistakeService = Depends(get_mistake_service),
):
    return await service.resolve_mistake(mistake_id)


@subtopic_router.patch("/{mistake_id}/revise", response_model=MistakeResponse)
async def revise_mistake(
    subtopic_id: UUID,
    mistake_id: UUID,
    service: MistakeService = Depends(get_mistake_service),
):
    return await service.revise_mistake(mistake_id)


@subtopic_router.delete("/{mistake_id}", status_code=204)
async def delete_mistake(
    subtopic_id: UUID,
    mistake_id: UUID,
    service: MistakeService = Depends(get_mistake_service),
):
    await service.delete_mistake(mistake_id)


# ── Goal-scoped routes ──

goal_router = APIRouter(
    prefix="/goals/{goal_id}/mistakes",
    tags=["Mistakes"],
)


@goal_router.get("", response_model=list[MistakeResponse])
async def get_mistakes_by_goal(
    goal_id: UUID,
    resolved: bool | None = Query(None),
    service: MistakeService = Depends(get_mistake_service),
):
    return await service.get_mistakes_by_goal(goal_id, resolved)
