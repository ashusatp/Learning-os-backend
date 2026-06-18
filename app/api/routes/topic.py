from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.topic_dependency import get_topic_service
from app.schema.topic_schema import CreateTopicRequest, UpdateTopicRequest, ReorderTopicsRequest, TopicResponse
from app.services.topic_service import TopicService

router = APIRouter(
    prefix="/subjects/{subject_id}/topics",
    tags=["Topics"],
)


@router.post("", response_model=TopicResponse, status_code=201)
async def create_topic(
    subject_id: UUID,
    payload: CreateTopicRequest,
    service: TopicService = Depends(get_topic_service),
):
    return await service.create_topic(
        subject_id=subject_id,
        name=payload.name,
        description=payload.description,
        order=payload.order,
    )


@router.get("", response_model=list[TopicResponse])
async def get_topics(
    subject_id: UUID,
    service: TopicService = Depends(get_topic_service),
):
    return await service.get_topics_by_subject(subject_id)


@router.put("/reorder", response_model=list[TopicResponse])
async def reorder_topics(
    subject_id: UUID,
    payload: ReorderTopicsRequest,
    service: TopicService = Depends(get_topic_service),
):
    return await service.reorder_topics(subject_id, payload.ordered_ids)


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    subject_id: UUID,
    topic_id: UUID,
    service: TopicService = Depends(get_topic_service),
):
    return await service.get_topic(topic_id)


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    subject_id: UUID,
    topic_id: UUID,
    payload: UpdateTopicRequest,
    service: TopicService = Depends(get_topic_service),
):
    return await service.update_topic(
        topic_id,
        **payload.model_dump(exclude_unset=True),
    )


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(
    subject_id: UUID,
    topic_id: UUID,
    service: TopicService = Depends(get_topic_service),
):
    await service.delete_topic(topic_id)
