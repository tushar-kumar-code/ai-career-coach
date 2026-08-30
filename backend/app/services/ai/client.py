from typing import Optional
from app.core.config import settings
from app.services.ai.base import BaseLLMProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.groq_provider import GroqProvider


class AIService:
    """Orchestrator for AI services, resolving the active LLM provider dynamically."""

    @classmethod
    def get_provider(
        cls,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> BaseLLMProvider:
        # Determine provider name: explicit param > settings.AI_PROVIDER > default 'groq'
        prov = (provider_type or settings.AI_PROVIDER or "groq").strip().lower()

        # If user explicitly passed an api_key, use it with the requested provider
        if prov == "gemini":
            key = api_key or settings.GEMINI_API_KEY
            return GeminiProvider(api_key=key)
        elif prov == "groq":
            key = api_key or settings.GROQ_API_KEY
            return GroqProvider(api_key=key, model=model or settings.GROQ_MODEL)
        else:
            # Fallback priority: Groq if key exists, otherwise Gemini
            if settings.GROQ_API_KEY:
                return GroqProvider(api_key=settings.GROQ_API_KEY, model=model or settings.GROQ_MODEL)
            return GeminiProvider(api_key=settings.GEMINI_API_KEY)
