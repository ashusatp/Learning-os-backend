from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.subtopic_dependency import get_subtopic_service
from app.schema.subtopic_schema import (
    CreateSubTopicRequest,
    UpdateSubTopicRequest,
    UpdatePerformanceRequest,
    ReorderSubTopicsRequest,
    SubTopicResponse,
)
from app.services.subtopic_service import SubTopicService

router = APIRouter(
    prefix="/topics/{topic_id}/subtopics",
    tags=["SubTopics"],
)


@router.post("", response_model=SubTopicResponse, status_code=201)
async def create_subtopic(
    topic_id: UUID,
    payload: CreateSubTopicRequest,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.create_subtopic(
        topic_id=topic_id,
        name=payload.name,
        description=payload.description,
        order=payload.order,
    )


@router.get("", response_model=list[SubTopicResponse])
async def get_subtopics(
    topic_id: UUID,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.get_subtopics_by_topic(topic_id)


@router.put("/reorder", response_model=list[SubTopicResponse])
async def reorder_subtopics(
    topic_id: UUID,
    payload: ReorderSubTopicsRequest,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.reorder_subtopics(topic_id, payload.ordered_ids)


@router.get("/{subtopic_id}", response_model=SubTopicResponse)
async def get_subtopic(
    topic_id: UUID,
    subtopic_id: UUID,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.get_subtopic(subtopic_id)


@router.put("/{subtopic_id}", response_model=SubTopicResponse)
async def update_subtopic(
    topic_id: UUID,
    subtopic_id: UUID,
    payload: UpdateSubTopicRequest,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.update_subtopic(
        subtopic_id,
        **payload.model_dump(exclude_unset=True),
    )


@router.delete("/{subtopic_id}", status_code=204)
async def delete_subtopic(
    topic_id: UUID,
    subtopic_id: UUID,
    service: SubTopicService = Depends(get_subtopic_service),
):
    await service.delete_subtopic(subtopic_id)


@router.post("/{subtopic_id}/revision", response_model=SubTopicResponse)
async def record_revision(
    topic_id: UUID,
    subtopic_id: UUID,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.record_revision(subtopic_id)


@router.patch("/{subtopic_id}/performance", response_model=SubTopicResponse)
async def update_performance(
    topic_id: UUID,
    subtopic_id: UUID,
    payload: UpdatePerformanceRequest,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.update_performance(
        subtopic_id=subtopic_id,
        questions_solved=payload.questions_solved,
        questions_correct=payload.questions_correct,
        mistake_count=payload.mistake_count,
    )
