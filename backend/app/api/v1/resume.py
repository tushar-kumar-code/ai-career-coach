from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.resume import Resume
from app.models.profile import UserProfile
from app.models.skill import Skill
from app.schemas.health import APIResponse
from app.schemas.resume import ResumeAnalysisResponse, ExtractedSkillSchema, BulletImprovementSchema
from app.services.resume.extractor import DocumentExtractor
from app.services.ai.resume_ai import ResumeAIService

router = APIRouter()
extractor = DocumentExtractor()
resume_ai_service = ResumeAIService()


@router.post(
    "/upload",
    response_model=APIResponse[ResumeAnalysisResponse],
    summary="Upload PDF/DOCX resume file and trigger analysis"
)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # 1. Validate & extract document text
    file_path, filename, raw_text = await extractor.process_uploaded_file(file, user_id)

    # 2. Save initial Resume entity
    resume = Resume(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        raw_text=raw_text
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    # 3. Execute Analysis Service
    analysis = await resume_ai_service.analyze_resume_text(
        db, user_id, resume.id, filename, raw_text
    )

    # 4. Update Resume Record in DB
    resume.overall_ats_score = analysis.ats_score
    resume.formatting_score = analysis.ats_breakdown.formatting_score
    resume.keyword_score = analysis.ats_breakdown.keyword_score
    resume.skills_score = analysis.ats_breakdown.skills_score
    resume.experience_score = analysis.ats_breakdown.experience_score
    resume.readability_score = analysis.ats_breakdown.readability_score
    resume.target_career_name = analysis.target_match.target_career_name
    resume.target_match_percentage = analysis.target_match.match_percentage
    resume.matching_skills = analysis.target_match.matching_skills
    resume.missing_skills = analysis.target_match.missing_skills
    resume.ats_breakdown_json = analysis.ats_breakdown.model_dump()
    resume.formatting_risk_flags = analysis.formatting_risk_flags
    resume.parsed_contact_info = analysis.contact_info.model_dump()
    resume.parsed_skills = [s.model_dump() for s in analysis.extracted_skills]
    resume.improvement_suggestions = [imp.model_dump() for imp in analysis.improvement_suggestions]

    db.add(resume)

    # 5. Persist Skills to Skill Table & Update UserProfile readiness
    for sk in analysis.extracted_skills:
        s_stmt = select(Skill).where(Skill.user_id == user_id, Skill.skill_name == sk.name)
        s_res = await db.execute(s_stmt)
        existing_skill = s_res.scalars().first()
        if not existing_skill:
            new_skill = Skill(
                user_id=user_id,
                skill_name=sk.name,
                category=sk.category,
                proficiency_percent=sk.proficiency_estimated,
                is_verified=True,
                evidence_sources=["Resume Extraction"]
            )
            db.add(new_skill)

    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()
    if user_profile:
        # Weighted readiness score updating profile
        composite_score = int((analysis.ats_score * 0.4) + (analysis.target_match.match_percentage * 0.6))
        user_profile.job_readiness_score = composite_score
        db.add(user_profile)

    await db.commit()

    # Recalculate Skill Profile & Gap Priorities
    try:
        from app.services.skill.ingestion_engine import SkillIngestionEngine
        from app.services.skill.gap_engine import SkillGapEngine
        u_skills = await SkillIngestionEngine().ingest_user_skills(db, user_id)
        await SkillGapEngine().calculate_skill_gaps(db, user_id, u_skills)
    except Exception as e:
        logger.warning(f"Background skill sync warning: {e}")

    return APIResponse(
        success=True,
        message="Resume uploaded and analyzed successfully",
        data=analysis
    )


@router.get(
    "/current",
    response_model=APIResponse[Optional[dict]],
    summary="Get user's current uploaded resume summary"
)
async def get_current_resume(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume:
        return APIResponse(
            success=True,
            message="No resume uploaded yet",
            data=None
        )

    resume_summary = {
        "id": resume.id,
        "filename": resume.filename,
        "overall_ats_score": resume.overall_ats_score,
        "target_career_name": resume.target_career_name,
        "target_match_percentage": resume.target_match_percentage,
        "uploaded_at": resume.created_at.isoformat() if resume.created_at else None
    }

    return APIResponse(
        success=True,
        message="Current resume retrieved",
        data=resume_summary
    )


@router.get(
    "/analysis",
    response_model=APIResponse[Optional[ResumeAnalysisResponse]],
    summary="Get full ATS breakdown and analysis for user's latest resume"
)
async def get_resume_analysis(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume or not resume.ats_breakdown_json:
        return APIResponse(
            success=False,
            message="No analyzed resume found for user",
            data=None
        )

    analysis_response = ResumeAnalysisResponse(
        id=resume.id,
        filename=resume.filename,
        ats_score=resume.overall_ats_score,
        ats_breakdown=resume.ats_breakdown_json,
        target_match={
            "target_career_name": resume.target_career_name or "Software Developer",
            "match_percentage": resume.target_match_percentage,
            "matching_skills": resume.matching_skills,
            "missing_skills": resume.missing_skills,
            "experience_alignment": "Matched skills with target role requirements.",
            "recommendation": f"Focus on adding missing skills: {', '.join(resume.missing_skills[:3]) if resume.missing_skills else 'None'}"
        },
        contact_info=resume.parsed_contact_info or {"name": "Candidate"},
        extracted_skills=resume.parsed_skills or [],
        formatting_risk_flags=resume.formatting_risk_flags or [],
        improvement_suggestions=resume.improvement_suggestions or []
    )

    return APIResponse(
        success=True,
        message="Resume analysis retrieved",
        data=analysis_response
    )


@router.post(
    "/improve",
    response_model=APIResponse[List[BulletImprovementSchema]],
    summary="Get AI bullet point improvement suggestions"
)
async def get_resume_improvements(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume:
        raise HTTPException(status_code=404, detail="No uploaded resume found")

    suggestions = resume.improvement_suggestions or []
    return APIResponse(
        success=True,
        message="Improvement suggestions generated",
        data=suggestions
    )


@router.get(
    "/skills",
    response_model=APIResponse[List[ExtractedSkillSchema]],
    summary="Get skills extracted from user's uploaded resume"
)
async def get_resume_skills(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume or not resume.parsed_skills:
        return APIResponse(
            success=True,
            message="No extracted skills found",
            data=[]
        )

    return APIResponse(
        success=True,
        message="Extracted skills retrieved",
        data=resume.parsed_skills
    )
