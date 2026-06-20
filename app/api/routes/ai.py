import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies.account_dependency import require_ai_access
from app.api.dependencies.ai_dependency import get_ai_service
from app.models.user import User
from app.schema.ai_schema import AIHelpRequest
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

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
        streamed = False
        try:
            async for chunk in ai_service.ai_help_stream(body, current_user.id):
                streamed = True
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.exception("Error during AI streaming")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if streamed:
                try:
                    await ai_service.record_usage(current_user.id)
                except Exception:
                    logger.exception("Failed to record AI usage")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
