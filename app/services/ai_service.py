import logging
from typing import AsyncGenerator
from uuid import UUID

from app.core.config import configs
from app.schema.ai_schema import AIHelpRequest
from app.services.ai.prompts import build_context_block, ai_help_system_prompt
from app.services.ai.provider import AIProvider
from app.services.account_service import AccountService

logger = logging.getLogger(__name__)


class AIService:

    def __init__(self, provider: AIProvider, account_service: AccountService):
        self.provider = provider
        self.account_service = account_service

    async def ai_help_stream(
        self, request: AIHelpRequest, user_id: UUID
    ) -> AsyncGenerator[str, None]:
        hierarchy = request.hierarchy.model_dump()
        context_block = build_context_block(hierarchy)
        system_prompt = ai_help_system_prompt(context_block)

        if request.current_notes_html:
            system_prompt += (
                f"\n\nThe student's current notes so far:\n{request.current_notes_html}"
            )

        if request.selected_text:
            system_prompt += (
                f"\n\nThe student has selected the following text from their notes and is asking about it:\n{request.selected_text}"
            )

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        logger.info(f"AI help stream started for user: {user_id}, context: {context_block}")

        async for chunk in self.provider.stream(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=configs.AI_MAX_TOKENS,
            temperature=configs.AI_TEMPERATURE,
        ):
            yield chunk

        logger.info(f"AI help stream completed for user: {user_id}")

    async def record_usage(self, user_id: UUID):
        """Call after streaming completes to increment the usage counter."""
        await self.account_service.increment_ai_usage(user_id)
