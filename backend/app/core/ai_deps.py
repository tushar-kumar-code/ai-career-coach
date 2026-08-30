from typing import Optional
from fastapi import Header, Request
from app.services.ai.base import BaseLLMProvider
from app.services.ai.client import AIService


async def get_ai_provider_from_headers(
    request: Request,
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key"),
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
) -> BaseLLMProvider:
    """Dependency that dynamically extracts AI Provider and API key from request headers."""
    # Check query params as secondary fallback if headers aren't used
    api_key = x_ai_api_key or request.query_params.get("api_key")
    provider = x_ai_provider or request.query_params.get("ai_provider")
    model = x_ai_model or request.query_params.get("ai_model")

    return AIService.get_provider(
        provider_type=provider,
        api_key=api_key,
        model=model
    )
