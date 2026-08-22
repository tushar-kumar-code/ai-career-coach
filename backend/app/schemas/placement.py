from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PlacementChecklistItem(BaseModel):
    key: str
    title: str
    description: str
    category: str
    completed: bool
    current_value: Optional[str] = None
    target_value: str
    action_title: str
    action_route: str


class PlacementChecklistResponse(BaseModel):
    overall_readiness_score: int
    readiness_tier: str
    tier_description: str
    completed_count: int
    total_count: int
    checklist_completion_percent: int
    items: List[PlacementChecklistItem]


class StudentCareerBriefSkill(BaseModel):
    name: str
    category: str
    proficiency_percent: int
    is_verified: bool
    confidence_status: str


class StudentCareerBriefProject(BaseModel):
    title: str
    difficulty: str
    expected_outcome: str
    resume_relevance: str


class StudentCareerBriefResponse(BaseModel):
    student_name: str
    target_career: str
    primary_archetype: str
    experience_level: str
    overall_readiness_score: int
    readiness_tier: str
    tier_description: str
    sub_scores: Dict[str, int]
    top_strengths: List[str]
    priority_gaps: List[str]
    critical_missing_skills: List[str]
    total_skills_count: int
    verified_skills_count: int
    verified_skills_sample: List[str]
    latest_resume_filename: Optional[str] = None
    latest_resume_ats_score: int = 0
    latest_resume_match_pct: int = 0
    roadmap_progress_percent: int = 0
    roadmap_completed_tasks: int = 0
    completed_projects: List[StudentCareerBriefProject] = Field(default_factory=list)
    interview_completed_count: int = 0
    interview_avg_score: int = 0
    interview_star_completed: bool = False
    active_applications_count: int = 0
    achievements_count: int = 0
    achievements_sample: List[str] = Field(default_factory=list)
    next_action: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str
