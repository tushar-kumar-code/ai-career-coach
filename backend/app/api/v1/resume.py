from typing import List, Optional
import uuid
import logging
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
from app.services.firestore.resume_repo import ResumeRepository
from app.services.firestore.skills_repo import SkillsRepository
from app.services.firestore.user_repo import UserRepository

router = APIRouter()
logger = logging.getLogger(__name__)
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
    # 1. Validate & extract document text (uploaded directly to Firebase Storage users/{uid}/resumes/{unique_filename})
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

    # 5. Persist to Firestore ResumeRepository
    try:
        resume_data = {
            "id": resume.id,
            "filename": filename,
            "file_path": file_path,
            "storage_path": file_path,
            "overall_ats_score": analysis.ats_score,
            "formatting_score": analysis.ats_breakdown.formatting_score,
            "keyword_score": analysis.ats_breakdown.keyword_score,
            "skills_score": analysis.ats_breakdown.skills_score,
            "experience_score": analysis.ats_breakdown.experience_score,
            "readability_score": analysis.ats_breakdown.readability_score,
            "target_career_name": analysis.target_match.target_career_name,
            "target_match_percentage": analysis.target_match.match_percentage,
            "matching_skills": analysis.target_match.matching_skills,
            "missing_skills": analysis.target_match.missing_skills,
            "ats_breakdown_json": analysis.ats_breakdown.model_dump(),
            "formatting_risk_flags": analysis.formatting_risk_flags,
            "parsed_contact_info": analysis.contact_info.model_dump(),
            "parsed_skills": [s.model_dump() for s in analysis.extracted_skills],
            "improvement_suggestions": [imp.model_dump() for imp in analysis.improvement_suggestions],
        }
        await ResumeRepository.save_resume(user_id, resume.id, resume_data)
    except Exception as e:
        logger.warning(f"Firestore resume save warning: {e}")

    # 6. Persist Skills to Firestore & SQL Skill Table & Update UserProfile readiness
    for sk in analysis.extracted_skills:
        try:
            await SkillsRepository.upsert_skill_by_name(
                user_id,
                sk.name,
                {
                    "category": sk.category,
                    "proficiency_percent": sk.proficiency_estimated,
                    "is_verified": True,
                    "evidence_sources": ["Resume Extraction"]
                }
            )
        except Exception as e:
            logger.warning(f"Firestore skill upsert warning for {sk.name}: {e}")

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

    composite_score = int((analysis.ats_score * 0.4) + (analysis.target_match.match_percentage * 0.6))
    try:
        await UserRepository.update_user_profile(user_id, {"job_readiness_score": composite_score})
    except Exception as e:
        logger.warning(f"Firestore user readiness update warning: {e}")

    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()
    if user_profile:
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
    # 1. Check Firestore first
    try:
        fs_resume = await ResumeRepository.get_latest_resume(user_id)
        if fs_resume:
            return APIResponse(
                success=True,
                message="Current resume retrieved",
                data={
                    "id": fs_resume.get("id"),
                    "filename": fs_resume.get("filename"),
                    "overall_ats_score": fs_resume.get("overall_ats_score"),
                    "target_career_name": fs_resume.get("target_career_name"),
                    "target_match_percentage": fs_resume.get("target_match_percentage"),
                    "uploaded_at": fs_resume.get("created_at")
                }
            )
    except Exception as e:
        logger.warning(f"Firestore get_latest_resume error: {e}")

    # 2. SQLite fallback
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume:
        demo_stmt = select(Resume).where(Resume.user_id == "demo-user-12345").order_by(Resume.created_at.desc())
        demo_res = await db.execute(demo_stmt)
        demo_resume = demo_res.scalars().first()
        if demo_resume:
            demo_resume.user_id = user_id
            db.add(demo_resume)
            await db.commit()
            resume = demo_resume

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
    # 1. Check Firestore first
    try:
        fs_resume = await ResumeRepository.get_latest_resume(user_id)
        if fs_resume and fs_resume.get("ats_breakdown_json"):
            analysis_response = ResumeAnalysisResponse(
                id=fs_resume.get("id"),
                filename=fs_resume.get("filename"),
                ats_score=fs_resume.get("overall_ats_score") or 0,
                ats_breakdown=fs_resume.get("ats_breakdown_json") or {},
                target_match={
                    "target_career_name": fs_resume.get("target_career_name") or "Software Developer",
                    "match_percentage": fs_resume.get("target_match_percentage") or 70,
                    "matching_skills": fs_resume.get("matching_skills") or [],
                    "missing_skills": fs_resume.get("missing_skills") or [],
                    "experience_alignment": "Matched skills with target role requirements.",
                    "recommendation": f"Focus on adding missing skills: {', '.join((fs_resume.get('missing_skills') or [])[:3]) if fs_resume.get('missing_skills') else 'None'}"
                },
                contact_info=fs_resume.get("parsed_contact_info") or {"name": "Candidate"},
                extracted_skills=fs_resume.get("parsed_skills") or [],
                formatting_risk_flags=fs_resume.get("formatting_risk_flags") or [],
                improvement_suggestions=fs_resume.get("improvement_suggestions") or []
            )
            return APIResponse(
                success=True,
                message="Resume analysis retrieved",
                data=analysis_response
            )
    except Exception as e:
        logger.warning(f"Firestore get_resume_analysis error: {e}")

    # 2. SQLite fallback
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume:
        demo_stmt = select(Resume).where(Resume.user_id == "demo-user-12345").order_by(Resume.created_at.desc())
        demo_res = await db.execute(demo_stmt)
        demo_resume = demo_res.scalars().first()
        if demo_resume and demo_resume.ats_breakdown_json:
            demo_resume.user_id = user_id
            db.add(demo_resume)
            await db.commit()
            await db.refresh(demo_resume)
            resume = demo_resume

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
    try:
        fs_resume = await ResumeRepository.get_latest_resume(user_id)
        if fs_resume and fs_resume.get("improvement_suggestions"):
            return APIResponse(
                success=True,
                message="Improvement suggestions generated",
                data=fs_resume.get("improvement_suggestions") or []
            )
    except Exception as e:
        logger.warning(f"Firestore get_resume_improvements error: {e}")

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
    try:
        fs_resume = await ResumeRepository.get_latest_resume(user_id)
        if fs_resume and fs_resume.get("parsed_skills"):
            return APIResponse(
                success=True,
                message="Extracted skills retrieved",
                data=fs_resume.get("parsed_skills")
            )
    except Exception as e:
        logger.warning(f"Firestore get_resume_skills error: {e}")

    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume:
        demo_stmt = select(Resume).where(Resume.user_id == "demo-user-12345").order_by(Resume.created_at.desc())
        demo_res = await db.execute(demo_stmt)
        demo_resume = demo_res.scalars().first()
        if demo_resume:
            demo_resume.user_id = user_id
            db.add(demo_resume)
            await db.commit()
            resume = demo_resume

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

