import json
import logging
from typing import Type, TypeVar, List, Dict, Any, Optional
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AIProviderException
from app.services.ai.base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]


class GroqProvider(BaseLLMProvider):
    """Groq AI Provider implementation using official groq SDK and direct HTTP fallback."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL or DEFAULT_GROQ_MODEL

    def _get_candidate_models(self) -> List[str]:
        models = [self.model]
        for m in GROQ_FALLBACK_MODELS:
            if m not in models:
                models.append(m)
        return models

    async def _direct_http_chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.5) -> str:
        """Direct REST fallback to Groq OpenAI-compatible endpoint."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"] or ""

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> str:
        if not self.api_key:
            logger.warning("Groq API Key is missing. Please configure your GROQ_API_KEY.")
            raise AIProviderException("Groq API key is not configured. Please add your Groq API key in AI Settings.")

        last_error = None
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        for model_name in self._get_candidate_models():
            try:
                try:
                    from groq import Groq
                    client = Groq(api_key=self.api_key, timeout=20.0)
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=0.4
                    )
                    self.model = model_name
                    return completion.choices[0].message.content or ""
                except Exception as sdk_err:
                    # Try direct HTTP fallback
                    content = await self._direct_http_chat(model=model_name, messages=messages, temperature=0.4)
                    self.model = model_name
                    return content
            except Exception as e:
                last_error = e
                logger.warning(f"Groq generation failed with model {model_name}: {e}. Trying fallback...")
                continue

        logger.error(f"Groq API error across all models: {str(last_error)}")
        raise AIProviderException(f"Groq generation error: {str(last_error)}")

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> str:
        """Handles multi-turn chat conversations with model fallback."""
        if not self.api_key:
            raise AIProviderException("Groq API key is not configured. Please add your Groq API key in AI Settings.")

        formatted_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            role = "assistant" if msg.get("role") in ["assistant", "ai"] else "user"
            formatted_messages.append({"role": role, "content": msg.get("content", "")})

        last_error = None
        for model_name in self._get_candidate_models():
            try:
                try:
                    from groq import Groq
                    client = Groq(api_key=self.api_key, timeout=20.0)
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=formatted_messages,
                        temperature=0.5
                    )
                    self.model = model_name
                    return completion.choices[0].message.content or ""
                except Exception as sdk_err:
                    content = await self._direct_http_chat(model=model_name, messages=formatted_messages, temperature=0.5)
                    self.model = model_name
                    return content
            except Exception as e:
                last_error = e
                logger.warning(f"Groq chat failed with model {model_name}: {e}. Trying fallback...")
                continue

        logger.error(f"Groq chat error across all models: {str(last_error)}")
        raise AIProviderException(f"Groq chat error: {str(last_error)}")

    async def generate_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_instruction: str = "You are an expert AI Career Coach."
    ) -> T:
        if not self.api_key:
            logger.warning("Groq API Key missing for structured generation.")
            raise AIProviderException("Groq API key is missing. Please configure your API key.")

        schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
        structured_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond ONLY with a valid JSON object matching this exact JSON Schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include any explanation or markdown formatting outside the raw JSON object."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": structured_prompt}
        ]

        last_error = None
        for model_name in self._get_candidate_models():
            try:
                raw_text = ""
                try:
                    from groq import Groq
                    client = Groq(api_key=self.api_key, timeout=20.0)
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.2
                    )
                    raw_text = completion.choices[0].message.content or "{}"
                except Exception:
                    # Direct HTTP fallback
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": model_name,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2
                    }
                    async with httpx.AsyncClient(timeout=25.0) as client:
                        resp = await client.post(url, headers=headers, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            raw_text = data["choices"][0]["message"]["content"] or "{}"
                        else:
                            raise Exception(f"HTTP {resp.status_code}: {resp.text}")

                clean_text = raw_text.strip()
                if clean_text.startswith("```"):
                    clean_text = clean_text.split("```")[1]
                    if clean_text.startswith("json"):
                        clean_text = clean_text[4:]
                    clean_text = clean_text.strip()

                parsed_json = json.loads(clean_text)
                self.model = model_name
                return output_schema.model_validate(parsed_json)
            except Exception as e:
                last_error = e
                logger.warning(f"Groq structured generation failed with model {model_name}: {e}. Trying fallback...")
                continue

        logger.error(f"Groq structured generation error across all models: {str(last_error)}")
        raise AIProviderException(f"Groq structured response failed: {str(last_error)}")
