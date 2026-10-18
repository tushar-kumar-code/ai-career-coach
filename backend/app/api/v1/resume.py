from typing import List, Optional
import uuid
import logging
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.resume import Resume
from app.models.profile import UserProfile
from app.models.skill import Skill
from app.schemas.health import APIResponse
from app.schemas.resume import (
    ResumeAnalysisResponse,
    ExtractedSkillSchema,
    BulletImprovementSchema,
    JobDescriptionMatchRequest,
    ATSBreakdownSchema,
    TargetCareerMatchSchema
)
from app.services.resume.extractor import DocumentExtractor
from app.services.ai.resume_ai import ResumeAIService
from app.services.firestore.resume_repo import ResumeRepository
from app.services.firestore.skills_repo import SkillsRepository
from app.services.firestore.user_repo import UserRepository
from app.services.skill.normalizer import SkillNormalizer

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
    job_description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # 1. Validate & extract document text in temporary RAM (no file saved to disk or Firebase Storage)
    try:
        file_path, filename, raw_text = await extractor.process_uploaded_file(file, user_id)

        # 2. Execute Groq AI Analysis & Structured Profile Extraction
        resume_id = str(uuid.uuid4())
        analysis = await resume_ai_service.analyze_resume_text(
            db, user_id, resume_id, filename, raw_text, job_description=job_description
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume processing error for user {user_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail="Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye."
        )

    # 3. Immediately discard raw resume text and transient buffers from RAM memory
    del raw_text
    import gc
    gc.collect()
    logger.info("🗑️ [RAM DISCARD] Raw resume file content and text immediately wiped from RAM memory.")

    # 4. Save Resume Record in SQL Database (ZERO resume files or text stored, only extracted profile structure)
    contact_info_dict = analysis.about_user.model_dump() if analysis.about_user else analysis.contact_info.model_dump()
    cert_list = [c.model_dump() for c in analysis.certifications]
    ach_list = [a.model_dump() for a in analysis.achievements]
    pub_list = [p.model_dump() for p in analysis.publications]
    lang_list = [l.model_dump() for l in analysis.languages]
    extra_list = [ex.model_dump() for ex in analysis.extracurriculars]

    contact_info_dict["certifications"] = cert_list
    contact_info_dict["achievements"] = ach_list
    contact_info_dict["publications"] = pub_list
    contact_info_dict["languages"] = lang_list
    contact_info_dict["extracurriculars"] = extra_list

    ats_breakdown_dict = analysis.ats_breakdown.model_dump()
    ats_breakdown_dict["certifications"] = cert_list
    ats_breakdown_dict["achievements"] = ach_list
    ats_breakdown_dict["publications"] = pub_list
    ats_breakdown_dict["languages"] = lang_list
    ats_breakdown_dict["extracurriculars"] = extra_list
    ats_breakdown_dict["suggested_domains"] = [d.model_dump() for d in analysis.suggested_domains]

    resume = Resume(
        id=resume_id,
        user_id=user_id,
        filename=filename,
        file_path=None,
        raw_text=None,
        formatted_text=None,
        overall_ats_score=analysis.ats_score,
        formatting_score=analysis.ats_breakdown.formatting_score,
        keyword_score=analysis.ats_breakdown.keyword_score,
        skills_score=analysis.ats_breakdown.skills_score,
        experience_score=analysis.ats_breakdown.experience_score,
        readability_score=analysis.ats_breakdown.readability_score,
        target_career_name=analysis.target_match.target_career_name,
        target_match_percentage=analysis.target_match.match_percentage,
        matching_skills=analysis.target_match.matching_skills,
        missing_skills=analysis.target_match.missing_skills,
        ats_breakdown_json=ats_breakdown_dict,
        formatting_risk_flags=analysis.formatting_risk_flags,
        parsed_contact_info=contact_info_dict,
        parsed_skills=[s.model_dump() for s in analysis.extracted_skills],
        parsed_experience=[e.model_dump() for e in analysis.experience],
        parsed_education=[ed.model_dump() for ed in analysis.education],
        parsed_projects=[p.model_dump() for p in analysis.projects],
        improvement_suggestions=[imp.model_dump() for imp in analysis.improvement_suggestions]
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    # 5. Persist Structured Candidate Profile & Analysis Metrics to Firestore (ZERO resume file stored)
    candidate_profile_dict = {
        "about_user": contact_info_dict,
        "skills": [s.model_dump() for s in analysis.extracted_skills],
        "experience": [e.model_dump() for e in analysis.experience],
        "projects": [p.model_dump() for p in analysis.projects],
        "education": [ed.model_dump() for ed in analysis.education],
        "certifications": cert_list,
        "achievements": ach_list,
        "publications": pub_list,
        "languages": lang_list,
        "extracurriculars": extra_list,
        "suggested_domains": [d.model_dump() for d in analysis.suggested_domains],
        "ats_score": analysis.ats_score,
        "filename": filename,
        "resume_id": resume_id
    }

    try:
        resume_data = {
            "id": resume.id,
            "filename": filename,
            "file_path": None,
            "storage_path": None,
            "raw_text": None,  # Resume file is NEVER stored in database
            "formatted_text": None,  # Resume file is NEVER stored in database
            "overall_ats_score": analysis.ats_score,
            "formatting_score": analysis.ats_breakdown.formatting_score,
            "keyword_score": analysis.ats_breakdown.keyword_score,
            "skills_score": analysis.ats_breakdown.skills_score,
            "experience_score": analysis.ats_breakdown.experience_score,
            "suggested_domains": [d.model_dump() for d in analysis.suggested_domains],
            "readability_score": analysis.ats_breakdown.readability_score,
            "target_career_name": analysis.target_match.target_career_name,
            "target_match_percentage": analysis.target_match.match_percentage,
            "matching_skills": analysis.target_match.matching_skills,
            "missing_skills": analysis.target_match.missing_skills,
            "ats_breakdown_json": ats_breakdown_dict,
            "formatting_risk_flags": analysis.formatting_risk_flags,
            "parsed_contact_info": candidate_profile_dict["about_user"],
            "parsed_skills": [s.model_dump() for s in analysis.extracted_skills],
            "parsed_experience": candidate_profile_dict["experience"],
            "parsed_projects": candidate_profile_dict["projects"],
            "parsed_education": candidate_profile_dict["education"],
            "parsed_certifications": candidate_profile_dict["certifications"],
            "parsed_achievements": candidate_profile_dict["achievements"],
            "parsed_publications": candidate_profile_dict["publications"],
            "parsed_languages": candidate_profile_dict["languages"],
            "parsed_extracurriculars": candidate_profile_dict["extracurriculars"],
            "about_user": candidate_profile_dict["about_user"],
            "improvement_suggestions": [imp.model_dump() for imp in analysis.improvement_suggestions],
        }
        await ResumeRepository.save_resume(user_id, resume.id, resume_data)
        logger.info("🔒 [STORAGE PRIVACY] Resume file NOT stored in Firestore or SQLite. Only extracted candidate profile retained.")
    except Exception as e:
        logger.warning(f"Firestore resume save warning: {e}")

    # 6. Persist Skills to Firestore & SQL Skill Table & Update UserProfile with Candidate Profile
    for sk in analysis.extracted_skills:
        norm_name = SkillNormalizer.normalize(sk.name)
        if not norm_name:
            continue
        prof_pct = sk.proficiency_estimated or 60
        prof_lvl = "Advanced" if prof_pct >= 80 else ("Intermediate" if prof_pct >= 60 else "Beginner")

        try:
            await SkillsRepository.upsert_skill_by_name(
                user_id,
                norm_name,
                {
                    "category": sk.category,
                    "proficiency_percent": prof_pct,
                    "proficiency_level": prof_lvl,
                    "confidence_status": "Claimed",
                    "evidence_sources": ["Resume Extraction"]
                }
            )
        except Exception as e:
            logger.warning(f"Firestore skill upsert warning for {norm_name}: {e}")

        s_stmt = select(Skill).where(
            Skill.user_id == user_id,
            (Skill.normalized_name == norm_name) | (Skill.skill_name.ilike(norm_name))
        )
        s_res = await db.execute(s_stmt)
        existing_skill = s_res.scalars().first()
        if not existing_skill:
            new_skill = Skill(
                user_id=user_id,
                skill_name=norm_name,
                normalized_name=norm_name,
                category=sk.category,
                proficiency_percent=prof_pct,
                proficiency_level=prof_lvl,
                confidence_score=45,
                confidence_status="Claimed",
                is_verified=False,
                evidence_sources=["Resume Extraction"]
            )
            db.add(new_skill)
        else:
            existing_skill.normalized_name = norm_name
            existing_skill.skill_name = norm_name
            if prof_pct > (existing_skill.proficiency_percent or 0):
                existing_skill.proficiency_percent = prof_pct
                existing_skill.proficiency_level = prof_lvl
            sources = list(set((existing_skill.evidence_sources or []) + ["Resume Extraction"]))
            existing_skill.evidence_sources = sources
            db.add(existing_skill)

    composite_score = int((analysis.ats_score * 0.4) + (analysis.target_match.match_percentage * 0.6))
    try:
        await UserRepository.update_user_profile(user_id, {
            "job_readiness_score": composite_score,
            "candidate_profile": candidate_profile_dict,
            "has_analyzed_resume": True,
            "is_analyzed": True
        })
        await UserRepository.upsert_user(user_id, {
            "has_completed_assessment": True,
            "has_uploaded_resume": True,
            "is_analyzed": True
        })
    except Exception as e:
        logger.warning(f"Firestore user readiness update warning: {e}")

    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()
    if user_profile:
        user_profile.job_readiness_score = composite_score
        skills_mat = dict(user_profile.skills_matrix or {})
        skills_mat["candidate_profile"] = candidate_profile_dict
        user_profile.skills_matrix = skills_mat
        if not user_profile.target_career and analysis.target_match.match_source != "none" and analysis.target_match.target_career_name:
            user_profile.target_career = analysis.target_match.target_career_name
        db.add(user_profile)
    else:
        user_profile = UserProfile(
            user_id=user_id,
            target_career=analysis.target_match.target_career_name if analysis.target_match.match_source != "none" else None,
            primary_archetype="The Builder",
            job_readiness_score=composite_score,
            skills_matrix={"candidate_profile": candidate_profile_dict}
        )
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

    # 7. Re-synthesize Career Domains combining Discovery Assessment + Uploaded Resume
    try:
        from app.models.assessment import AssessmentResponse
        from app.services.ai.discovery_ai import ai_service
        from app.services.firestore.assessment_repo import AssessmentRepository
        a_stmt = select(AssessmentResponse).where(
            AssessmentResponse.user_id == user_id,
            AssessmentResponse.status == "COMPLETED"
        ).order_by(AssessmentResponse.updated_at.desc())
        a_res = await db.execute(a_stmt)
        completed_session = a_res.scalars().first()
        if completed_session and completed_session.dimension_answers:
            logger.info("Synthesizing Career Domains from uploaded Resume + existing Discovery Assessment...")
            dual_ai_result = await ai_service.analyze_assessment(
                db,
                completed_session.dimension_answers,
                resume_profile=candidate_profile_dict,
                language="en"
            )
            completed_session.role_recommendations = [r.model_dump() for r in dual_ai_result.recommended_careers]
            completed_session.ai_analysis_json = dual_ai_result.model_dump()
            db.add(completed_session)
            if user_profile:
                user_profile.recommended_roles = [r.model_dump() for r in dual_ai_result.recommended_careers]
                db.add(user_profile)
            await db.commit()

            try:
                await AssessmentRepository.save_assessment(user_id, completed_session.id, {
                    "role_recommendations": [r.model_dump() for r in dual_ai_result.recommended_careers],
                    "ai_analysis_json": dual_ai_result.model_dump()
                })
                await UserRepository.update_user_profile(user_id, {
                    "recommended_roles": [r.model_dump() for r in dual_ai_result.recommended_careers]
                })
            except Exception as fe:
                logger.warning(f"Firestore career update after resume upload warning: {fe}")
    except Exception as e:
        logger.warning(f"Career domain synthesis after resume upload error: {e}")

    return APIResponse(
        success=True,
        message="Resume verified, structured profile created, and analyzed successfully",
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
            contact_data = fs_resume.get("about_user") or fs_resume.get("parsed_contact_info") or {"name": "Candidate"}
            target_name = fs_resume.get("target_career_name")
            is_general = not target_name or target_name in ["None Selected (General Mode)", "none", "None"]

            target_match_data = {
                "target_career_name": "None Selected (General Mode)" if is_general else target_name,
                "match_percentage": 0 if is_general else (fs_resume.get("target_match_percentage") or 0),
                "matching_skills": fs_resume.get("matching_skills") or [],
                "missing_skills": fs_resume.get("missing_skills") or [],
                "experience_alignment": "General resume evaluation mode active. No target career specified." if is_general else f"Matched skills against {target_name} requirements.",
                "recommendation": "Select a target career from Career Discovery or paste a job description to see role-specific matching." if is_general else f"Focus on adding missing skills: {', '.join((fs_resume.get('missing_skills') or [])[:3]) if fs_resume.get('missing_skills') else 'None'}",
                "match_source": "none" if is_general else "catalog",
                "preferred_skills_matching": (fs_resume.get("ats_breakdown_json") or {}).get("preferred_skills_matching", []),
                "preferred_skills_missing": (fs_resume.get("ats_breakdown_json") or {}).get("preferred_skills_missing", [])
            }

            suggested_domains_raw = fs_resume.get("suggested_domains") or (fs_resume.get("ats_breakdown_json") or {}).get("suggested_domains")
            if not suggested_domains_raw:
                suggested_domains_raw = [
                    d.model_dump() for d in resume_ai_service.generate_domain_suggestions(
                        extracted_skills=fs_resume.get("parsed_skills") or [],
                        projects=fs_resume.get("parsed_projects") or [],
                        experience=fs_resume.get("parsed_experience") or [],
                        education=fs_resume.get("parsed_education") or []
                    )
                ]

            analysis_response = ResumeAnalysisResponse(
                id=fs_resume.get("id"),
                filename=fs_resume.get("filename"),
                ats_score=fs_resume.get("overall_ats_score") or 0,
                ats_breakdown=fs_resume.get("ats_breakdown_json") or {},
                target_match=target_match_data,
                contact_info=contact_data,
                extracted_skills=fs_resume.get("parsed_skills") or [],
                formatting_risk_flags=fs_resume.get("formatting_risk_flags") or [],
                improvement_suggestions=fs_resume.get("improvement_suggestions") or [],
                formatted_text=None,
                raw_text=None,
                about_user=contact_data,
                experience=fs_resume.get("parsed_experience") or [],
                projects=fs_resume.get("parsed_projects") or [],
                education=fs_resume.get("parsed_education") or [],
                certifications=fs_resume.get("parsed_certifications") or [],
                achievements=fs_resume.get("parsed_achievements") or [],
                publications=fs_resume.get("parsed_publications") or [],
                languages=fs_resume.get("parsed_languages") or [],
                extracurriculars=fs_resume.get("parsed_extracurriculars") or [],
                suggested_domains=suggested_domains_raw
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

    if not resume and user_id == "demo-user-12345":
        demo_stmt = select(Resume).where(Resume.user_id == "demo-user-12345").order_by(Resume.created_at.desc())
        demo_res = await db.execute(demo_stmt)
        demo_resume = demo_res.scalars().first()
        if demo_resume and demo_resume.ats_breakdown_json:
            resume = demo_resume

    if not resume or not resume.ats_breakdown_json:
        return APIResponse(
            success=False,
            message="No analyzed resume found for user",
            data=None
        )

    contact_data = resume.parsed_contact_info or {"name": "Candidate"}
    ats_dict = resume.ats_breakdown_json or {}
    certs = contact_data.get("certifications") or ats_dict.get("certifications") or []
    achievements = contact_data.get("achievements") or ats_dict.get("achievements") or []
    publications = contact_data.get("publications") or ats_dict.get("publications") or []
    languages = contact_data.get("languages") or ats_dict.get("languages") or []
    extracurriculars = contact_data.get("extracurriculars") or ats_dict.get("extracurriculars") or []
    projects = resume.parsed_projects or contact_data.get("projects") or ats_dict.get("projects") or []

    target_name = resume.target_career_name
    is_general = not target_name or target_name in ["None Selected (General Mode)", "none", "None"]

    target_match_data = {
        "target_career_name": "None Selected (General Mode)" if is_general else target_name,
        "match_percentage": 0 if is_general else (resume.target_match_percentage or 0),
        "matching_skills": resume.matching_skills or [],
        "missing_skills": resume.missing_skills or [],
        "experience_alignment": "General resume evaluation mode active. No target career specified." if is_general else f"Matched skills against {target_name} requirements.",
        "recommendation": "Select a target career from Career Discovery or paste a job description to see role-specific matching." if is_general else f"Focus on adding missing skills: {', '.join((resume.missing_skills or [])[:3]) if resume.missing_skills else 'None'}",
        "match_source": "none" if is_general else "catalog",
        "preferred_skills_matching": (resume.ats_breakdown_json or {}).get("preferred_skills_matching", []),
        "preferred_skills_missing": (resume.ats_breakdown_json or {}).get("preferred_skills_missing", [])
    }

    suggested_domains_sql = (resume.ats_breakdown_json or {}).get("suggested_domains")
    if not suggested_domains_sql:
        suggested_domains_sql = [
            d.model_dump() for d in resume_ai_service.generate_domain_suggestions(
                extracted_skills=resume.parsed_skills or [],
                projects=projects,
                experience=resume.parsed_experience or [],
                education=resume.parsed_education or []
            )
        ]

    analysis_response = ResumeAnalysisResponse(
        id=resume.id,
        filename=resume.filename,
        ats_score=resume.overall_ats_score,
        ats_breakdown=resume.ats_breakdown_json,
        target_match=target_match_data,
        contact_info=contact_data,
        extracted_skills=resume.parsed_skills or [],
        formatting_risk_flags=resume.formatting_risk_flags or [],
        improvement_suggestions=resume.improvement_suggestions or [],
        formatted_text=None,
        raw_text=None,
        about_user=contact_data,
        experience=resume.parsed_experience or [],
        projects=projects,
        education=resume.parsed_education or [],
        certifications=certs,
        achievements=achievements,
        publications=publications,
        languages=languages,
        extracurriculars=extracurriculars,
        suggested_domains=suggested_domains_sql
    )

    return APIResponse(
        success=True,
        message="Resume analysis retrieved",
        data=analysis_response
    )


@router.post(
    "/match-jd",
    response_model=APIResponse[ResumeAnalysisResponse],
    summary="Match existing uploaded resume against a specific Job Description"
)
async def match_job_description(
    request: JobDescriptionMatchRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Evaluates candidate's existing uploaded resume against a specific pasted Job Description.
    Calculates Mode A Job-Specific ATS score and requirements match without needing to re-upload document.
    """
    if not request.job_description or len(request.job_description.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Job description must be at least 20 characters long."
        )

    # 1. Fetch user's latest resume from SQLite or Firestore
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    fs_resume = None
    if not resume:
        fs_resume = await ResumeRepository.get_latest_resume(user_id)
        if not fs_resume:
            raise HTTPException(
                status_code=404,
                detail="No analyzed resume found. Please upload a resume first before matching against a job description."
            )

    contact_info = (resume.parsed_contact_info if resume else fs_resume.get("about_user")) or {}
    raw_skills = (resume.parsed_skills if resume else fs_resume.get("parsed_skills")) or []
    experience = (resume.parsed_experience if resume else fs_resume.get("parsed_experience")) or []
    projects = (resume.parsed_projects if resume else fs_resume.get("parsed_projects")) or contact_info.get("projects") or []
    education = (resume.parsed_education if resume else fs_resume.get("parsed_education")) or []
    certifications = (fs_resume.get("parsed_certifications") if fs_resume else []) or contact_info.get("certifications") or []
    achievements = (fs_resume.get("parsed_achievements") if fs_resume else []) or contact_info.get("achievements") or []
    publications = (fs_resume.get("parsed_publications") if fs_resume else []) or contact_info.get("publications") or []
    languages = (fs_resume.get("parsed_languages") if fs_resume else []) or contact_info.get("languages") or []
    extracurriculars = (fs_resume.get("parsed_extracurriculars") if fs_resume else []) or contact_info.get("extracurriculars") or []

    skill_names = [s.get("name") if isinstance(s, dict) else str(s) for s in raw_skills if s]

    # Reconstruct parsed dict for ATS engine
    parsed = {
        "contact_info": contact_info,
        "skills": skill_names,
        "experience": experience,
        "projects": projects,
        "education": education,
        "summary": contact_info.get("summary", "")
    }

    # Build simulated text representation for keyword overlap analysis
    simulated_text = (
        f"{contact_info.get('summary', '')}\n"
        f"Skills: {', '.join(skill_names)}\n"
        f"Experience:\n" + "\n".join([f"{e.get('role', '')} {e.get('company', '')} {e.get('description', '')}" for e in experience if isinstance(e, dict)]) + "\n"
        f"Projects:\n" + "\n".join([f"{p.get('title', '')} {p.get('description', '')} {', '.join(p.get('technologies', []))}" for p in projects if isinstance(p, dict)]) + "\n"
        f"Education:\n" + "\n".join([f"{ed.get('degree', '')} {ed.get('institution', '')}" for ed in education if isinstance(ed, dict)])
    )

    # 2. Evaluate ATS against Specific Job Description (Mode A)
    ats_breakdown, risk_flags = resume_ai_service.ats_engine.evaluate_resume(
        parsed_resume=parsed,
        raw_text=simulated_text,
        target_role="Specific Job Description Vacancy",
        job_description=request.job_description
    )

    # 3. Match against Target Job Description
    target_match = await resume_ai_service.target_matcher.match_resume_to_target(
        db=db,
        user_id=user_id,
        resume_skills=skill_names,
        job_description=request.job_description
    )

    # 4. Generate improvements
    improvements = resume_ai_service.improver.generate_improvements(
        parsed, target_match.missing_skills
    )

    # 5. Update SQLite record if present
    if resume:
        resume.overall_ats_score = ats_breakdown.overall_ats_score
        resume.formatting_score = ats_breakdown.formatting_score
        resume.keyword_score = ats_breakdown.keyword_score
        resume.skills_score = ats_breakdown.skills_score
        resume.experience_score = ats_breakdown.experience_score
        resume.readability_score = ats_breakdown.readability_score
        resume.target_career_name = target_match.target_career_name
        resume.target_match_percentage = target_match.match_percentage
        resume.matching_skills = target_match.matching_skills
        resume.missing_skills = target_match.missing_skills
        resume.ats_breakdown_json = ats_breakdown.model_dump()
        resume.improvement_suggestions = [imp.model_dump() for imp in improvements]
        db.add(resume)
        await db.commit()

    # 6. Update Firestore record
    try:
        resume_id = resume.id if resume else fs_resume.get("id")
        await ResumeRepository.save_resume(user_id, resume_id, {
            "overall_ats_score": ats_breakdown.overall_ats_score,
            "formatting_score": ats_breakdown.formatting_score,
            "keyword_score": ats_breakdown.keyword_score,
            "skills_score": ats_breakdown.skills_score,
            "experience_score": ats_breakdown.experience_score,
            "readability_score": ats_breakdown.readability_score,
            "target_career_name": target_match.target_career_name,
            "target_match_percentage": target_match.match_percentage,
            "matching_skills": target_match.matching_skills,
            "missing_skills": target_match.missing_skills,
            "ats_breakdown_json": ats_breakdown.model_dump(),
            "improvement_suggestions": [imp.model_dump() for imp in improvements]
        })
    except Exception as e:
        logger.warning(f"Firestore update after match-jd notice: {e}")

    analysis_response = ResumeAnalysisResponse(
        id=resume.id if resume else fs_resume.get("id"),
        filename=resume.filename if resume else fs_resume.get("filename", "Resume"),
        ats_score=ats_breakdown.overall_ats_score,
        ats_breakdown=ats_breakdown,
        target_match=target_match,
        contact_info=contact_info,
        extracted_skills=raw_skills,
        formatting_risk_flags=risk_flags,
        improvement_suggestions=improvements,
        formatted_text=None,
        raw_text=None,
        about_user=contact_info,
        experience=experience,
        projects=projects,
        education=education,
        certifications=certifications,
        achievements=achievements,
        publications=publications,
        languages=languages,
        extracurriculars=extracurriculars,
        suggested_domains=[
            d.model_dump() for d in resume_ai_service.generate_domain_suggestions(
                extracted_skills=raw_skills,
                projects=projects,
                experience=experience,
                education=education
            )
        ]
    )

    return APIResponse(
        success=True,
        message="Resume successfully evaluated against specific job description",
        data=analysis_response
    )


@router.get(
    "/profile",
    response_model=APIResponse[Optional[dict]],
    summary="Get user's extracted candidate profile from resume"
)
async def get_candidate_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Returns candidate profile (About User, Skills, Experience, Projects, Education, Certs, Achievements, etc.) extracted from resume."""
    # 1. Check user profile in Firestore
    try:
        user_doc = await UserRepository.get_user(user_id)
        if user_doc and user_doc.get("candidate_profile"):
            return APIResponse(
                success=True,
                message="Candidate profile retrieved from Firestore",
                data=user_doc.get("candidate_profile")
            )
    except Exception as e:
        logger.warning(f"Firestore get_candidate_profile notice: {e}")

    # 2. Check latest resume in Firestore
    try:
        fs_resume = await ResumeRepository.get_latest_resume(user_id)
        if fs_resume:
            profile_data = {
                "about_user": fs_resume.get("about_user") or fs_resume.get("parsed_contact_info") or {"name": "Candidate"},
                "skills": fs_resume.get("parsed_skills") or [],
                "experience": fs_resume.get("parsed_experience") or [],
                "projects": fs_resume.get("parsed_projects") or [],
                "education": fs_resume.get("parsed_education") or [],
                "certifications": fs_resume.get("parsed_certifications") or [],
                "achievements": fs_resume.get("parsed_achievements") or [],
                "publications": fs_resume.get("parsed_publications") or [],
                "languages": fs_resume.get("parsed_languages") or [],
                "extracurriculars": fs_resume.get("parsed_extracurriculars") or [],
                "ats_score": fs_resume.get("overall_ats_score") or 0,
                "filename": fs_resume.get("filename") or "Resume"
            }
            return APIResponse(
                success=True,
                message="Candidate profile retrieved",
                data=profile_data
            )
    except Exception as e:
        logger.warning(f"Firestore get_candidate_profile fallback notice: {e}")

    # 3. SQLite fallback
    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
    res = await db.execute(stmt)
    resume = res.scalars().first()

    if not resume:
        return APIResponse(
            success=False,
            message="No resume profile available. Please upload your resume first.",
            data=None
        )

    contact_data = resume.parsed_contact_info or {"name": "Candidate"}
    ats_dict = resume.ats_breakdown_json or {}
    certs = contact_data.get("certifications") or ats_dict.get("certifications") or []
    achievements = contact_data.get("achievements") or ats_dict.get("achievements") or []
    publications = contact_data.get("publications") or ats_dict.get("publications") or []
    languages = contact_data.get("languages") or ats_dict.get("languages") or []
    extracurriculars = contact_data.get("extracurriculars") or ats_dict.get("extracurriculars") or []
    projects = resume.parsed_projects or contact_data.get("projects") or ats_dict.get("projects") or []

    profile_data = {
        "about_user": contact_data,
        "skills": resume.parsed_skills or [],
        "experience": resume.parsed_experience or [],
        "projects": projects,
        "education": resume.parsed_education or [],
        "certifications": certs,
        "achievements": achievements,
        "publications": publications,
        "languages": languages,
        "extracurriculars": extracurriculars,
        "ats_score": resume.overall_ats_score,
        "filename": resume.filename
    }

    return APIResponse(
        success=True,
        message="Candidate profile retrieved",
        data=profile_data
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

