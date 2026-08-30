import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.health import APIResponse
from app.services.ai.client import AIService

router = APIRouter()
logger = logging.getLogger(__name__)


class TestKeyRequest(BaseModel):
    provider: str = Field(..., description="'groq' or 'gemini'")
    api_key: str = Field(..., description="API key to test")
    model: Optional[str] = Field(default=None, description="Optional model override")


class TestKeyResponse(BaseModel):
    valid: bool
    provider: str
    message: str
    model: Optional[str] = None


class AIConfigResponse(BaseModel):
    configured_provider: str
    has_groq_key: bool
    has_gemini_key: bool
    default_groq_model: str
    available_providers: list[str] = ["groq", "gemini"]


@router.get("/ai-config", response_model=APIResponse[AIConfigResponse], summary="Get AI configuration status")
async def get_ai_config():
    return APIResponse(
        success=True,
        data=AIConfigResponse(
            configured_provider=settings.AI_PROVIDER,
            has_groq_key=bool(settings.GROQ_API_KEY),
            has_gemini_key=bool(settings.GEMINI_API_KEY),
            default_groq_model=settings.GROQ_MODEL,
            available_providers=["groq", "gemini"]
        )
    )


@router.post("/test-key", response_model=APIResponse[TestKeyResponse], summary="Test and validate an AI API Key")
async def test_ai_key(req: TestKeyRequest):
    provider_name = req.provider.strip().lower()
    api_key = req.api_key.strip()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key cannot be empty"
        )

    try:
        provider_instance = AIService.get_provider(
            provider_type=provider_name,
            api_key=api_key,
            model=req.model
        )

        test_prompt = "Say 'AI connection verified successfully' in one sentence."
        response_text = await provider_instance.generate_text(
            prompt=test_prompt,
            system_instruction="You are an AI assistant performing a health check connection test. Respond briefly."
        )

        return APIResponse(
            success=True,
            data=TestKeyResponse(
                valid=True,
                provider=provider_name.upper(),
                message=f"Key verified successfully! Response: {response_text.strip()}",
                model=getattr(provider_instance, "model", None)
            ),
            message=f"{provider_name.upper()} API Key is valid and active"
        )
    except Exception as e:
        logger.warning(f"Key validation failed for {provider_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate {provider_name.upper()} API key: {str(e)}"
        )
