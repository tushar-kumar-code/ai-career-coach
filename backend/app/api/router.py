from fastapi import APIRouter
from app.api.v1 import health, assessment, resume, skills, roadmap, jobs

api_router = APIRouter()

# Include version 1 routers
api_router.include_router(health.router, prefix="", tags=["Health Diagnostics"])
api_router.include_router(assessment.router, prefix="/assessment", tags=["Career Discovery Assessment"])
api_router.include_router(resume.router, prefix="/resume", tags=["Resume Intelligence System"])
api_router.include_router(skills.router, prefix="/skills", tags=["Skill Intelligence System"])
api_router.include_router(roadmap.router, prefix="/roadmap", tags=["Personalized Career Roadmap System"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Job Intelligence System"])
