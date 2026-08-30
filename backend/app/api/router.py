from fastapi import APIRouter
from app.api.v1 import health, assessment, resume, skills, roadmap, jobs, interview, digital_twin, placement, chat, settings_ai, auth

api_router = APIRouter()

# Include version 1 routers
api_router.include_router(health.router, prefix="", tags=["Health Diagnostics"])
api_router.include_router(auth.router, prefix="/auth", tags=["User Authentication & Security"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Career Coach Contextual Chat"])
api_router.include_router(settings_ai.router, prefix="/settings", tags=["AI Settings & Key Management"])
api_router.include_router(assessment.router, prefix="/assessment", tags=["Career Discovery Assessment"])
api_router.include_router(resume.router, prefix="/resume", tags=["Resume Intelligence System"])
api_router.include_router(skills.router, prefix="/skills", tags=["Skill Intelligence System"])
api_router.include_router(roadmap.router, prefix="/roadmap", tags=["Personalized Career Roadmap System"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Job Intelligence System"])
api_router.include_router(interview.router, prefix="/interview", tags=["AI Mock Interview & Adaptive Engine"])
api_router.include_router(digital_twin.router, prefix="/digital-twin", tags=["Career Digital Twin & Progress Engine"])
api_router.include_router(placement.router, prefix="/placement", tags=["College Placement Readiness & Brief Engine"])

