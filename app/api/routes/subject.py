from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.subject_dependency import get_subject_service
from app.schema.subject_schema import CreateSubjectRequest, UpdateSubjectRequest, SubjectResponse
from app.services.subject_service import SubjectService

router = APIRouter(
    prefix="/goals/{goal_id}/subjects",
    tags=["Subjects"],
)


@router.post("", response_model=SubjectResponse, status_code=201)
async def create_subject(
    goal_id: UUID,
    payload: CreateSubjectRequest,
    service: SubjectService = Depends(get_subject_service),
):
    return await service.create_subject(
        goal_id=goal_id,
        name=payload.name,
        description=payload.description,
        order=payload.order,
    )


@router.get("", response_model=list[SubjectResponse])
async def get_subjects(
    goal_id: UUID,
    include_archived: bool = False,
    service: SubjectService = Depends(get_subject_service),
):
    return await service.get_subjects_by_goal(goal_id, include_archived=include_archived)


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    goal_id: UUID,
    subject_id: UUID,
    service: SubjectService = Depends(get_subject_service),
):
    return await service.get_subject(subject_id)


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    goal_id: UUID,
    subject_id: UUID,
    payload: UpdateSubjectRequest,
    service: SubjectService = Depends(get_subject_service),
):
    return await service.update_subject(
        subject_id,
        **payload.model_dump(exclude_unset=True),
    )


@router.patch("/{subject_id}/archive", response_model=SubjectResponse)
async def archive_subject(
    goal_id: UUID,
    subject_id: UUID,
    archive: bool = True,
    service: SubjectService = Depends(get_subject_service),
):
    return await service.archive_subject(subject_id, archive)


@router.delete("/{subject_id}", status_code=204)
async def delete_subject(
    goal_id: UUID,
    subject_id: UUID,
    service: SubjectService = Depends(get_subject_service),
):
    await service.delete_subject(subject_id)
