from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.schemas.health import APIResponse
from app.schemas.skill import (
    UserSkillSchema,
    SkillProfileResponse,
    SkillDetailResponse,
    SkillEvidenceSchema,
    SkillGapSchema
)
from app.services.skill.ingestion_engine import SkillIngestionEngine
from app.services.skill.gap_engine import SkillGapEngine

router = APIRouter()
ingestion_engine = SkillIngestionEngine()
gap_engine = SkillGapEngine()


@router.get(
    "",
    response_model=APIResponse[List[UserSkillSchema]],
    summary="Get all user skills"
)
async def get_user_skills(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Skill).where(Skill.user_id == user_id)
    res = await db.execute(stmt)
    skills = res.scalars().all()

    schema_list = [
        UserSkillSchema(
            id=s.id,
            skill_name=s.skill_name,
            normalized_name=s.normalized_name,
            category=s.category,
            proficiency_percent=s.proficiency_percent,
            proficiency_level=s.proficiency_level,
            confidence_score=s.confidence_score,
            confidence_status=s.confidence_status,
            target_required_level=s.target_required_level,
            gap_status=s.gap_status or "Matched",
            priority=s.priority or "Low",
            priority_reason=s.priority_reason,
            evidence_sources=s.evidence_sources or []
        )
        for s in skills
    ]

    return APIResponse(
        success=True,
        message="User skills retrieved successfully",
        data=schema_list
    )


@router.get(
    "/profile",
    response_model=APIResponse[SkillProfileResponse],
    summary="Get full user skill profile with confidence levels and target gaps"
)
async def get_skill_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # 1. Ingest skills if empty or sync
    stmt = select(Skill).where(Skill.user_id == user_id)
    res = await db.execute(stmt)
    user_skills = res.scalars().all()

    if not user_skills:
        user_skills = await ingestion_engine.ingest_user_skills(db, user_id)

    # 2. Calculate gaps & priorities
    target_career, strong_skills, skills_to_improve, missing_gaps, recommended_next = await gap_engine.calculate_skill_gaps(
        db, user_id, user_skills
    )

    verified_cnt = sum(1 for s in user_skills if s.confidence_status == "Verified")
    supported_cnt = sum(1 for s in user_skills if s.confidence_status == "Supported")
    claimed_cnt = sum(1 for s in user_skills if s.confidence_status == "Claimed")

    profile_response = SkillProfileResponse(
        user_id=user_id,
        target_career=target_career,
        total_skills_count=len(user_skills),
        verified_count=verified_cnt,
        supported_count=supported_cnt,
        claimed_count=claimed_cnt,
        strong_skills=strong_skills,
        skills_to_improve=skills_to_improve,
        missing_skills=missing_gaps,
        recommended_next_skills=recommended_next
    )

    return APIResponse(
        success=True,
        message="Skill profile retrieved successfully",
        data=profile_response
    )


@router.get(
    "/gaps",
    response_model=APIResponse[List[SkillGapSchema]],
    summary="Get skill gaps relative to user's selected Target Career"
)
async def get_skill_gaps(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Skill).where(Skill.user_id == user_id)
    res = await db.execute(stmt)
    user_skills = res.scalars().all()

    _, _, _, missing_gaps, _ = await gap_engine.calculate_skill_gaps(db, user_id, user_skills)

    return APIResponse(
        success=True,
        message="Skill gaps calculated successfully",
        data=missing_gaps
    )


@router.get(
    "/recommended",
    response_model=APIResponse[List[UserSkillSchema]],
    summary="Get top priority skills recommended to learn next"
)
async def get_recommended_skills(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Skill).where(Skill.user_id == user_id)
    res = await db.execute(stmt)
    user_skills = res.scalars().all()

    _, _, _, _, recommended_next = await gap_engine.calculate_skill_gaps(db, user_id, user_skills)

    return APIResponse(
        success=True,
        message="Recommended skills retrieved",
        data=recommended_next
    )


@router.get(
    "/{skill_id}",
    response_model=APIResponse[SkillDetailResponse],
    summary="Get detailed view and evidence records for a specific skill"
)
async def get_skill_details(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Skill).where(Skill.id == skill_id, Skill.user_id == user_id)
    res = await db.execute(stmt)
    skill = res.scalars().first()

    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found for user")

    e_stmt = select(SkillEvidence).where(SkillEvidence.user_skill_id == skill.id)
    e_res = await db.execute(e_stmt)
    evidences = e_res.scalars().all()

    evidence_schemas = [
        SkillEvidenceSchema(
            id=e.id,
            source=e.source,
            description=e.description,
            confidence_weight=e.confidence_weight,
            evidence_date=e.created_at.isoformat() if e.created_at else None
        )
        for e in evidences
    ]

    skill_schema = UserSkillSchema(
        id=skill.id,
        skill_name=skill.skill_name,
        normalized_name=skill.normalized_name,
        category=skill.category,
        proficiency_percent=skill.proficiency_percent,
        proficiency_level=skill.proficiency_level,
        confidence_score=skill.confidence_score,
        confidence_status=skill.confidence_status,
        target_required_level=skill.target_required_level,
        gap_status=skill.gap_status or "Matched",
        priority=skill.priority or "Low",
        priority_reason=skill.priority_reason,
        evidence_sources=skill.evidence_sources or []
    )

    next_action = (
        f"Build a hands-on project using {skill.skill_name} to increase confidence from {skill.confidence_status} to Verified."
        if skill.confidence_status != "Verified" else
        f"Continue applying {skill.skill_name} in complex system scenarios."
    )

    return APIResponse(
        success=True,
        message="Skill details retrieved",
        data=SkillDetailResponse(
            skill=skill_schema,
            evidence_records=evidence_schemas,
            target_career_requirement=skill.target_required_level or "Required",
            recommended_next_action=next_action
        )
    )


@router.post(
    "/recalculate",
    response_model=APIResponse[SkillProfileResponse],
    summary="Recalculate skill profile & gap priorities across all data sources"
)
async def recalculate_skill_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    user_skills = await ingestion_engine.ingest_user_skills(db, user_id)
    target_career, strong_skills, skills_to_improve, missing_gaps, recommended_next = await gap_engine.calculate_skill_gaps(
        db, user_id, user_skills
    )

    verified_cnt = sum(1 for s in user_skills if s.confidence_status == "Verified")
    supported_cnt = sum(1 for s in user_skills if s.confidence_status == "Supported")
    claimed_cnt = sum(1 for s in user_skills if s.confidence_status == "Claimed")

    profile_response = SkillProfileResponse(
        user_id=user_id,
        target_career=target_career,
        total_skills_count=len(user_skills),
        verified_count=verified_cnt,
        supported_count=supported_cnt,
        claimed_count=claimed_cnt,
        strong_skills=strong_skills,
        skills_to_improve=skills_to_improve,
        missing_skills=missing_gaps,
        recommended_next_skills=recommended_next
    )

    return APIResponse(
        success=True,
        message="Skill profile recalculated successfully",
        data=profile_response
    )
