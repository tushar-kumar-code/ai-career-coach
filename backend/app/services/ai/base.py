from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract Base Class for interchangeable AI Providers (Gemini, OpenAI, Anthropic, etc.)."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> str:
        """Generate unstructured text from the LLM."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_instruction: str = "You are an expert AI Career Coach. Return responses matching the requested JSON schema."
    ) -> T:
        """Generate structured data strictly validated against a Pydantic schema."""
        pass
