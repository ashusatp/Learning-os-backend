import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator

from app.core.config import configs
from app.exceptions.custom_exceptions import BadRequestException

logger = logging.getLogger(__name__)


class AIProvider(ABC):

    @abstractmethod
    async def stream(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]: ...


class OpenAIProvider(AIProvider):

    def __init__(self):
        from openai import AsyncOpenAI

        if not configs.OPENAI_API_KEY:
            raise BadRequestException("OpenAI API key is not configured")

        self.client = AsyncOpenAI(api_key=configs.OPENAI_API_KEY)
        self.model = configs.OPENAI_MODEL

    async def stream(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        formatted_messages = [{"role": "system", "content": system_prompt}]
        formatted_messages.extend(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.exception("OpenAI streaming error")
            raise BadRequestException(f"OpenAI error: {str(e)}")


class AnthropicProvider(AIProvider):

    def __init__(self):
        from anthropic import AsyncAnthropic

        if not configs.ANTHROPIC_API_KEY:
            raise BadRequestException("Anthropic API key is not configured")

        self.client = AsyncAnthropic(api_key=configs.ANTHROPIC_API_KEY)
        self.model = configs.ANTHROPIC_MODEL

    async def stream(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        try:
            async with self.client.messages.stream(
                model=self.model,
                system=system_prompt,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.exception("Anthropic streaming error")
            raise BadRequestException(f"Anthropic error: {str(e)}")


class GeminiProvider(AIProvider):

    def __init__(self):
        from google import genai

        if not configs.GEMINI_API_KEY:
            raise BadRequestException("Gemini API key is not configured")

        self.client = genai.Client(api_key=configs.GEMINI_API_KEY)
        self.model = configs.GEMINI_MODEL

    async def stream(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        from google.genai import types

        contents = []

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])],
            ))

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        try:
            async for chunk in self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.exception("Gemini streaming error")
            raise BadRequestException(f"Gemini error: {str(e)}")
