import json
import logging
from typing import Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AIProviderException
from app.services.ai.base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini AI Provider implementation using google-genai or HTTP fallback."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> str:
        if not self.api_key:
            logger.warning("Gemini API Key is missing. Returning structured fallback/mock response for development.")
            return "AI Provider response: Gemini API key is not configured. Please set GEMINI_API_KEY."

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_instruction}\n\n{prompt}"
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise AIProviderException(f"Gemini generation failed: {str(e)}")

    async def generate_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> T:
        if not self.api_key:
            logger.warning("Gemini API Key missing for structured generation. Attempting mock fallback.")
            # For development when API key is not yet set, return dummy instance if possible
            try:
                return output_schema.model_construct()
            except Exception:
                raise AIProviderException("Gemini API Key not set and default schema construction failed.")

        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
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
