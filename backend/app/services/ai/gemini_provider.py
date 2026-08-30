import json
import logging
from typing import Type, TypeVar, List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AIProviderException
from app.services.ai.base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini AI Provider implementation using google-genai."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or "gemini-2.5-flash"

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> str:
        if not self.api_key:
            raise AIProviderException("Gemini API key is not configured. Please add your Gemini API key in AI Settings.")

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=f"{system_instruction}\n\n{prompt}"
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise AIProviderException(f"Gemini generation failed: {str(e)}")

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> str:
        """Handles multi-turn chat conversations using Gemini."""
        if not self.api_key:
            raise AIProviderException("Gemini API key is not configured. Please add your Gemini API key in AI Settings.")

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            
            # Format contents
            conversation_text = f"System: {system_instruction}\n\n"
            for msg in messages:
                role_label = "Assistant" if msg.get("role") in ["assistant", "ai"] else "User"
                conversation_text += f"{role_label}: {msg.get('content', '')}\n"
            conversation_text += "Assistant: "

            response = client.models.generate_content(
                model=self.model,
                contents=conversation_text
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini chat error: {str(e)}")
            raise AIProviderException(f"Gemini chat error: {str(e)}")

    async def generate_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> T:
        if not self.api_key:
            raise AIProviderException("Gemini API key is not configured. Please add your Gemini API key in AI Settings.")

        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=f"{system_instruction}\n\n{prompt}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=output_schema,
                ),
            )
            parsed_data = json.loads(response.text)
            return output_schema.model_validate(parsed_data)
        except Exception as e:
            logger.error(f"Gemini structured output error: {str(e)}")
            raise AIProviderException(f"Gemini structured response failed: {str(e)}")
