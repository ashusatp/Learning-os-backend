import logging
import uuid as uuid_mod
from pathlib import Path, PurePosixPath
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.api.dependencies.auth_dependency import get_current_user
from app.api.dependencies.issue_dependency import get_issue_service
from app.core.config import configs
from app.exceptions.custom_exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.schema.issue_schema import IssueResponse
from app.services.issue_service import IssueService

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/webm", "video/quicktime",
}
VALID_CATEGORIES = {"bug", "feature", "ui", "performance", "other"}
MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20MB per file
MAX_ATTACHMENTS = 3

router = APIRouter(
    prefix="/issues",
    tags=["Issues"],
)


@router.post("", response_model=IssueResponse, status_code=201)
async def create_issue(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(default="bug"),
    page_url: Optional[str] = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    service: IssueService = Depends(get_issue_service),
):
    if category not in VALID_CATEGORIES:
        raise BadRequestException(f"Invalid category: {category}")

    if len(files) > MAX_ATTACHMENTS:
        raise BadRequestException(f"Maximum {MAX_ATTACHMENTS} attachments allowed")

    attachments = []

    for file in files:
        if not file.filename:
            continue

        content_type = file.content_type or ""
        if content_type not in ALLOWED_TYPES:
            raise BadRequestException(
                f"File type '{content_type}' not allowed. Only images and videos are accepted."
            )

        content = await file.read()
        if len(content) > MAX_ATTACHMENT_SIZE:
            raise BadRequestException(
                f"File '{file.filename}' exceeds 20MB limit"
            )

        upload_dir = Path(configs.UPLOAD_DIR) / "issues"
        upload_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename).suffix
        disk_name = f"{uuid_mod.uuid4().hex}{ext}"
        file_path = upload_dir / disk_name

        with open(file_path, "wb") as f:
            f.write(content)

        attachments.append({
            "original_name": file.filename,
            "disk_name": disk_name,
            "content_type": content_type,
            "size": len(content),
        })

    return await service.create_issue(
        user_id=current_user.id,
        title=title.strip(),
        description=description.strip(),
        page_url=page_url,
        category=category,
        attachments=attachments,
    )


@router.get("/attachments/{filename}")
async def get_attachment(filename: str):
    # Prevent path traversal
    safe_name = PurePosixPath(filename).name
    if safe_name != filename or not filename:
        raise BadRequestException("Invalid filename")

    file_path = Path(configs.UPLOAD_DIR) / "issues" / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise NotFoundException("Attachment not found")
    return FileResponse(file_path)
