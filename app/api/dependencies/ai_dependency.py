from fastapi import Depends

from app.api.dependencies.account_dependency import get_account_service
from app.services.account_service import AccountService
from app.services.ai.factory import get_ai_provider
from app.services.ai_service import AIService


def get_ai_service(
    account_service: AccountService = Depends(get_account_service),
) -> AIService:
    provider = get_ai_provider()
    return AIService(provider, account_service)
