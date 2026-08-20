from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class JobSchema(BaseModel):
    id: str
    provider_id: Optional[str] = None
    provider_name: str = "catalog"
    title: str
    company: str
    location: str = "Remote"
    is_remote: bool = True
    employment_type: str = "Full-time"
    experience_level: str = "Mid Level"
    description: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    education_requirements: str = "Bachelor's degree or equivalent experience"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    source_url: Optional[str] = None
    posted_date: Optional[str] = None
    is_saved: bool = False
    application_status: Optional[str] = None  # Saved, Applied, Assessment, Interview, Offer, Rejected, Withdrawn


class JobSearchQuery(BaseModel):
    query: Optional[str] = None
    location: Optional[str] = None
    remote_only: Optional[bool] = None
    experience_level: Optional[str] = None
    provider_name: Optional[str] = None


class JobMatchBreakdown(BaseModel):
    overall_score: int
    skill_score: int
    career_alignment_score: int
    resume_score: int
    experience_score: int
    roadmap_score: int
    readiness_status: str  # READY, NEARLY READY, NEEDS SKILL DEVELOPMENT, LOW MATCH
    readiness_explanation: str


class RoadmapGapConnection(BaseModel):
    skill_name: str
    gap_level: str  # Essential, Core, Optional
    roadmap_phase: str  # Phase 1, Phase 2, etc.
    estimated_weeks: int
    match_boost_percent: int


class JobMatchAnalysisResponse(BaseModel):
    job: JobSchema
    match_breakdown: JobMatchBreakdown
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    strong_matches_explanation: List[str] = Field(default_factory=list)
    missing_gaps_explanation: List[str] = Field(default_factory=list)
    roadmap_connections: List[RoadmapGapConnection] = Field(default_factory=list)
    recommendation: str


class SavedJobResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    notes: Optional[str] = None
    saved_at: str
    job: JobSchema


class JobApplicationCreateRequest(BaseModel):
    job_id: str
    status: str = "Applied"  # Saved, Applied, Assessment, Interview, Offer, Rejected, Withdrawn
    applied_date: Optional[str] = None
    interview_date: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None


class JobApplicationUpdateRequest(BaseModel):
    status: Optional[str] = None
    applied_date: Optional[str] = None
    interview_date: Optional[str] = None
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    job_title: str
    company: str
    location: str
    status: str
    applied_date: Optional[str] = None
    interview_date: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    match_percentage: int = 75
    readiness_status: str = "NEARLY READY"
    created_at: str
    updated_at: str


class ApplicationHistoryResponse(BaseModel):
    id: str
    application_id: str
    from_status: Optional[str] = None
    to_status: str
    changed_at: str
    notes: Optional[str] = None
