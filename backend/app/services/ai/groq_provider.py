import json
import logging
from typing import Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AIProviderException
from app.services.ai.base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq AI Provider implementation using official groq SDK with Llama 3.3 70B model."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL or "llama-3.3-70b-versatile"

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> str:
        if not self.api_key:
            logger.warning("Groq API Key is missing. Returning structured fallback for development.")
            return "AI Provider response: Groq API key is not configured."

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise AIProviderException(f"Groq generation failed: {str(e)}")

    async def generate_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> T:
        if not self.api_key:
            logger.warning("Groq API Key missing for structured generation. Returning constructed schema fallback.")
            try:
                return output_schema.model_construct()
            except Exception:
                raise AIProviderException("Groq API Key not set.")

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            
            schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
            structured_prompt = (
                f"{prompt}\n\n"
                f"You MUST respond ONLY with a valid JSON object matching this exact JSON Schema:\n"
                f"```json\n{schema_json}\n```\n"
                f"Do not include any explanation or markdown code block formatting outside the raw JSON object."
            )

            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": structured_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            raw_text = completion.choices[0].message.content or "{}"
            logger.info(f"Groq raw structured response received ({len(raw_text)} chars)")
            
            # Clean markdown codeblocks if model included them despite json_object mode
            clean_text = raw_text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
                clean_text = clean_text.strip()

            parsed_json = json.loads(clean_text)
            return output_schema.model_validate(parsed_json)
        except Exception as e:
            logger.error(f"Groq structured generation error: {str(e)}")
            raise AIProviderException(f"Groq structured response failed: {str(e)}")
