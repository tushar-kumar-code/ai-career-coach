from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SkillEvidenceSchema(BaseModel):
    id: str
    source: str  # Resume, Assessment, Project, Interview
    description: str
    confidence_weight: int
    evidence_date: Optional[str] = None


class UserSkillSchema(BaseModel):
    id: str
    skill_name: str
    normalized_name: str
    category: str
    proficiency_percent: int
    proficiency_level: str  # Beginner, Intermediate, Advanced
    confidence_score: int
    confidence_status: str  # Claimed, Supported, Verified
    target_required_level: Optional[str] = None
    gap_status: str  # Matched, Partially Matched, Missing, Weak
    priority: str  # High, Medium, Low
    priority_reason: Optional[str] = None
    evidence_sources: List[str]
    last_evaluated_at: Optional[str] = None



class SkillGapSchema(BaseModel):
    skill_name: str
    category: str
    current_proficiency: str
    required_proficiency: str
    gap_status: str
    priority: str
    priority_reason: str


class SkillProfileResponse(BaseModel):
    user_id: str
    target_career: str
    total_skills_count: int
    verified_count: int
    supported_count: int
    claimed_count: int
    strong_skills: List[UserSkillSchema]
    skills_to_improve: List[UserSkillSchema]
    missing_skills: List[SkillGapSchema]
    recommended_next_skills: List[UserSkillSchema]


class SkillDetailResponse(BaseModel):
    skill: UserSkillSchema
    evidence_records: List[SkillEvidenceSchema]
    target_career_requirement: str
    recommended_next_action: str
