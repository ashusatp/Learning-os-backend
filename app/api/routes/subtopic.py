import logging
import os
import uuid as uuid_mod
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse

from app.api.dependencies.subtopic_dependency import get_subtopic_service
from app.core.config import configs
from app.exceptions.custom_exceptions import BadRequestException, NotFoundException
from app.models.subtopic_file import SubtopicFile
from app.schema.subtopic_schema import (
    CreateSubTopicRequest,
    UpdateSubTopicRequest,
    UpdatePerformanceRequest,
    ReorderSubTopicsRequest,
    SaveNotesRequest,
    SubTopicResponse,
    SubtopicFileResponse,
)
from app.services.subtopic_service import SubTopicService

logger = logging.getLogger(__name__)

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
        questions_correct=payload.questions_correct,
        mistake_count=payload.mistake_count,
    )


# ── Notes endpoints ──


@router.put("/{subtopic_id}/notes", response_model=SubTopicResponse)
async def save_notes(
    topic_id: UUID,
    subtopic_id: UUID,
    payload: SaveNotesRequest,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.save_notes(
        subtopic_id=subtopic_id,
        notes_html=payload.notes_html,
        sketch_data_url=payload.sketch_data_url,
        whiteboard_data_url=payload.whiteboard_data_url,
    )


# ── File endpoints ──


@router.post(
    "/{subtopic_id}/files",
    response_model=SubtopicFileResponse,
    status_code=201,
)
async def upload_file(
    topic_id: UUID,
    subtopic_id: UUID,
    file: UploadFile = File(...),
    service: SubTopicService = Depends(get_subtopic_service),
):
    max_bytes = configs.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Read file content
    content = await file.read()
    if len(content) > max_bytes:
        raise BadRequestException(
            f"File too large. Maximum size is {configs.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Create upload directory
    upload_dir = Path(configs.UPLOAD_DIR) / str(subtopic_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save to disk with unique name
    ext = Path(file.filename or "file").suffix
    disk_name = f"{uuid_mod.uuid4().hex}{ext}"
    file_path = upload_dir / disk_name

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"File saved to disk: {file_path}")

    return await service.create_file(
        subtopic_id=subtopic_id,
        original_name=file.filename or "file",
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
        storage_path=str(file_path),
        disk_name=disk_name,
    )


@router.get("/{subtopic_id}/files", response_model=list[SubtopicFileResponse])
async def list_files(
    topic_id: UUID,
    subtopic_id: UUID,
    service: SubTopicService = Depends(get_subtopic_service),
):
    return await service.get_files(subtopic_id)


@router.get("/{subtopic_id}/files/{file_id}/download")
async def download_file(
    topic_id: UUID,
    subtopic_id: UUID,
    file_id: UUID,
    service: SubTopicService = Depends(get_subtopic_service),
):
    file_record = await service.get_file(file_id)
    if not os.path.exists(file_record.storage_path):
        raise NotFoundException("File not found on disk")
    return FileResponse(
        path=file_record.storage_path,
        filename=file_record.original_name,
        media_type=file_record.content_type,
    )


@router.delete("/{subtopic_id}/files/{file_id}", status_code=204)
async def delete_file(
    topic_id: UUID,
    subtopic_id: UUID,
    file_id: UUID,
    service: SubTopicService = Depends(get_subtopic_service),
):
    await service.delete_file(file_id)
