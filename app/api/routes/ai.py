import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies.account_dependency import require_ai_access
from app.api.dependencies.ai_dependency import get_ai_service
from app.models.user import User
from app.schema.ai_schema import AIHelpRequest
from app.services.ai_service import AIService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post("/help")
async def ai_help(
    body: AIHelpRequest,
    current_user: User = Depends(require_ai_access),
    ai_service: AIService = Depends(get_ai_service),
):
    async def event_stream():
        async for chunk in ai_service.ai_help_stream(body, current_user.id):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
