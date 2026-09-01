import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.ai_deps import get_ai_provider_from_headers
from app.services.ai.base import BaseLLMProvider
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

    # 1. Fetch User Profile Context
    stmt_prof = select(UserProfile).where(UserProfile.user_id == user_id)
    res_prof = await db.execute(stmt_prof)
    profile = res_prof.scalar_one_or_none()

    target_career = req.target_role or (profile.target_career if profile and profile.target_career else "Software Developer")
    user_skills = list((profile.skills_matrix or {}).keys()) if profile and profile.skills_matrix else []

    # 2. Fetch User Resume Context
    stmt_res = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res_res = await db.execute(stmt_res)
    resume = res_res.scalars().first()
    ats_score = resume.overall_ats_score if resume else None

    # 3. Fetch User Roadmap Context
    stmt_rm = select(Roadmap).where(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc())
    res_rm = await db.execute(stmt_rm)
    roadmap = res_rm.scalars().first()
    roadmap_progress = getattr(roadmap, "overall_progress_percent", getattr(roadmap, "progress_percentage", 0)) if roadmap else 0

    lang_rule = ""
    if x_language_preference == "hi":
        lang_rule = "\n3. **Language Preference**: The candidate's selected language preference is Hindi. Write your entire response, explanations, action steps, and advice in clear, supportive Hindi (with standard technical terms in English script where appropriate)."

    # Build Contextual System Prompt with strict formatting rules for readability
    system_instruction = f"""You are an elite, encouraging, and deeply technical AI Career Coach for university students and early-career developers.
Candidate Context:
- Target Career Role: {target_career}
- Candidate Verified Skills: {', '.join(user_skills[:10]) if user_skills else 'Beginner / In Progress'}
- Resume ATS Score: {f'{ats_score}%' if ats_score is not None else 'Not yet uploaded'}
- Roadmap Completion: {roadmap_progress}%

FORMATTING & RESPONSE GUIDELINES (CRITICAL FOR USER EXPERIENCE):
1. **Visual Clarity & Structure**:
   - Organize every response using clean Markdown headers with emojis (e.g., `### 🎯 Quick Summary`, `### 📌 Step-by-Step Action Plan`, `### 💡 Pro Tip & Best Practice`, `### 💻 Code / Technical Example`).
   - Use bullet points (`- ` or `* `) and numbered lists (`1. `, `2. `) instead of long walls of text.
   - Highlight important keywords, technologies, or concepts in **bold**.
   - When providing code, ALWAYS wrap it inside standard fenced code blocks with the language specified (e.g. ```python, ```javascript, ```sql).

2. **Tone & Style**:
   - Be practical, motivating, concise, and solution-oriented.
   - Break down complex technical concepts into intuitive, easy-to-digest explanations.
   - End with a friendly, relevant follow-up question or suggestion to keep the conversation engaging.
{lang_rule}
"""

    # Prepare chat message history
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

        # Smart built-in fallback response so user is never stranded
        fallback_reply = (
            f"### 🎯 Strategic Guidance for **{target_career}**\n\n"
            f"Here is a structured overview to level up your profile and interview readiness:\n\n"
            f"### 📌 Priority Action Items\n"
            f"1. **Core Technical Competencies**: Strengthen key domain fundamentals including {', '.join(user_skills[:4]) if user_skills else 'Data Structures, Algorithms, System Architecture, and API Design'}.\n"
            f"2. **Production-Grade Projects**: Build full-stack or end-to-end applications demonstrating clean code, caching, and database design.\n"
            f"3. **Mock Interview Drills**: Practice behavioral STAR-method and live technical questions in the **Mock Interview** tab.\n\n"
            f"### 💡 Pro Tip\n"
            f"> Keep your resume ATS-optimized by tailoring keyword density to target job descriptions!\n\n"
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
