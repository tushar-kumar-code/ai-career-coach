from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthCheckResponse, APIResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=APIResponse[HealthCheckResponse],
    summary="System Health Diagnostics",
    description="Check backend status, environment configuration, real database ping, and AI provider configuration."
)
async def check_health(db: AsyncSession = Depends(get_db)):
    # 1. Real Database Ping Test
    db_status = "disconnected"

    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. AI Provider Configuration Check (Groq 70B model)
    if settings.AI_PROVIDER == "groq":
        if settings.GROQ_API_KEY:
            ai_status = f"groq ({settings.GROQ_MODEL}, configured)"
        else:
            ai_status = "groq (unconfigured)"
    elif settings.AI_PROVIDER == "gemini":
        ai_status = "gemini (configured)" if settings.GEMINI_API_KEY else "gemini (unconfigured)"
    else:
        ai_status = settings.AI_PROVIDER

    health_data = HealthCheckResponse(
        status="ok",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        database=db_status,
        ai_provider=ai_status
    )
    
    return APIResponse(
        success=True,
        message="AI Career Coach API health check completed",
        data=health_data
    )
