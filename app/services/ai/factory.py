from app.core.config import configs
from app.exceptions.custom_exceptions import BadRequestException
from app.services.ai.provider import AIProvider, OpenAIProvider, AnthropicProvider, GeminiProvider


def get_ai_provider() -> AIProvider:
    provider = configs.AI_PROVIDER.lower()

    if provider == "openai":
        return OpenAIProvider()
    elif provider == "anthropic":
        return AnthropicProvider()
    elif provider == "gemini":
        return GeminiProvider()
    else:
        raise BadRequestException(f"Unsupported AI provider: {provider}")
