import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.ai_deps import get_ai_provider_from_headers
from app.services.ai.base import BaseLLMProvider
from app.services.ai.chat_context import build_candidate_chat_dossier, format_chat_system_instruction
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.roadmap import Roadmap
from app.schemas.health import APIResponse
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=APIResponse[ChatResponse], summary="Chat with Contextual AI Career Coach")
async def chat_with_coach(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    ai_provider: BaseLLMProvider = Depends(get_ai_provider_from_headers),
    x_language_preference: str = Header(default="en", alias="X-Language-Preference")
):
    if not req.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    # 1. Build Comprehensive Candidate Intelligence Dossier (Resume + Assessment + Skills + Roadmap)
    dossier = await build_candidate_chat_dossier(db, user_id, target_role_override=req.target_role)

    # 2. Build Deeply Contextual System Instruction for Groq / AI Provider
    system_instruction = format_chat_system_instruction(dossier, language=x_language_preference)

    # 3. Prepare chat message history
    messages_payload = []
    if req.history:
        for item in req.history[-8:]:  # keep last 8 messages for context
            messages_payload.append({
                "role": "assistant" if item.role in ["assistant", "ai"] else "user",
                "content": item.content
            })
    messages_payload.append({"role": "user", "content": req.message})

    try:
        if hasattr(ai_provider, "generate_chat"):
            ai_reply = await ai_provider.generate_chat(
                messages=messages_payload,
                system_instruction=system_instruction
            )
        else:
            # Fallback for simple generate_text
            full_prompt = f"User asks: {req.message}"
            ai_reply = await ai_provider.generate_text(
                prompt=full_prompt,
                system_instruction=system_instruction
            )

        provider_name = ai_provider.__class__.__name__.replace("Provider", "")
        return APIResponse(
            success=True,
            data=ChatResponse(
                response=ai_reply.strip(),
                provider=provider_name,
                timestamp=datetime.now().strftime("%I:%M %p")
            ),
            message="Message generated successfully"
        )
    except Exception as e:
        logger.error(f"Chat generation failed: {str(e)}")
        error_msg = str(e)
        
        # If API key missing / invalid, raise a clear 400 error
        if "API key" in error_msg or "not configured" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI API Key is missing or invalid. Please click 'Set API Key' in the header to enter your free Groq or Gemini key."
            )

        # Smart built-in fallback response referencing candidate profile
        name = dossier.get("name") or "there"
        target_role = dossier.get("target_career") or "Software Developer"
        skills = [s["name"] for s in (dossier.get("verified_skills") or [])[:3]]
        skills_str = ", ".join(skills) if skills else "core software engineering fundamentals"
        missing = (dossier.get("resume_data") or {}).get("missing_skills") or []
        missing_str = f" Focus on bridging gaps in: **{', '.join(missing[:3])}**." if missing else ""

        fallback_reply = (
            f"### 🎯 Strategic Guidance for **{target_role}**\n\n"
            f"Hello **{name}**! Here is tailored guidance based on your analyzed profile:\n\n"
            f"### 📌 Priority Action Items\n"
            f"1. **Core Competencies**: Keep building on your verified skills in {skills_str}.{missing_str}\n"
            f"2. **Production Projects**: Strengthen your resume projects by highlighting measurable results and clean architecture.\n"
            f"3. **Mock Practice**: Drill targeted technical questions in the **Mock Interview** tab.\n\n"
            f"### 💡 Next Step\n"
            f"> What specific part of your {target_role} journey would you like to drill down into right now?\n\n"
            f"*Note: Live LLM was temporarily busy. You can retry or verify your API key in AI settings.*"
        )

        return APIResponse(
            success=True,
            data=ChatResponse(
                response=fallback_reply,
                provider="AI Assistant (Fallback)",
                timestamp=datetime.now().strftime("%I:%M %p")
            ),
            message="Fallback guidance generated"
        )
