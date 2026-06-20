from app.core.config import configs
from app.exceptions.custom_exceptions import BadRequestException
from app.services.ai.provider import AIProvider, OpenAIProvider, AnthropicProvider, GeminiProvider

_cached_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    global _cached_provider
    if _cached_provider is not None:
        return _cached_provider

    provider = configs.AI_PROVIDER.lower()

    if provider == "openai":
        _cached_provider = OpenAIProvider()
    elif provider == "anthropic":
        _cached_provider = AnthropicProvider()
    elif provider == "gemini":
        _cached_provider = GeminiProvider()
    else:
        raise BadRequestException(f"Unsupported AI provider: {provider}")

    return _cached_provider
