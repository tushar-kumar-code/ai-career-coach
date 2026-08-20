from app.core.config import settings
from app.services.ai.base import BaseLLMProvider
from app.services.ai.gemini_provider import GeminiProvider


class AIService:
    """Orchestrator for AI services, abstracting concrete LLM provider implementation."""

    _instance: BaseLLMProvider = None

    @classmethod
    def get_provider(cls) -> BaseLLMProvider:
        if cls._instance is None:
            provider_type = settings.AI_PROVIDER.lower()
            if provider_type == "gemini":
                cls._instance = GeminiProvider()
            else:
                # Default to GeminiProvider as primary backend choice
                cls._instance = GeminiProvider()
        return cls._instance
