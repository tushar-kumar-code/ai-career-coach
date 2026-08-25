from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RoadmapGenerateRequest(BaseModel):
    hours_per_day: int = Field(default=1, ge=1, le=8, description="Available study hours per day")
    days_per_week: int = Field(default=5, ge=1, le=7, description="Available study days per week")
    preferred_learning_style: str = Field(default="Hands-on", description="Hands-on, Visual, or Reading")


class RoadmapPreferencesRequest(BaseModel):
    hours_per_day: int = Field(..., ge=1, le=8)
    days_per_week: int = Field(..., ge=1, le=7)
    preferred_learning_style: str = Field(...)


class RoadmapTaskSchema(BaseModel):
    id: str
    title: str
    description: str
    estimated_minutes: int
    task_type: str
    why_it_matters: str
    is_completed: bool
    completed_at: Optional[str] = None
    # Learning resource fields (Phase 3 — optional so existing tasks still serialize)
    concept_explanation: Optional[str] = None
    practice_exercise: Optional[str] = None
    check_quiz_question: Optional[str] = None
    check_quiz_options: Optional[List[str]] = None
    check_quiz_answer: Optional[str] = None
    # Priority flag from Interview feedback loop
    is_priority: Optional[bool] = False
    priority_reason: Optional[str] = None


class RoadmapProjectSchema(BaseModel):
    id: str
    title: str
    objective: str
    skills_practiced: List[str]
    difficulty: str
    expected_outcome: str
    resume_relevance: str
    is_completed: bool


class RoadmapMilestoneSchema(BaseModel):
    id: str
    title: str
    criteria: str
    is_completed: bool


class RoadmapPhaseSchema(BaseModel):
    id: str
    phase_number: int
    title: str
    type: str
    skills: List[str]
    learning_objectives: List[str]
    progress_percent: int
    tasks: List[RoadmapTaskSchema]
    project: Optional[RoadmapProjectSchema] = None
    milestone: Optional[RoadmapMilestoneSchema] = None


class RoadmapResponse(BaseModel):
    id: str
    user_id: str
    target_role: str
    overall_progress_percent: int
    is_active: bool
    is_outdated: bool
    hours_per_day: int
    days_per_week: int
    preferred_learning_style: str
    total_estimated_weeks: int
    phases: List[RoadmapPhaseSchema]
    completed_task_ids: List[str]
    completed_milestone_ids: List[str]
    completed_project_ids: List[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TodayFocusResponse(BaseModel):
    target_career: str
    today_focus_title: str
    current_phase_id: Optional[str] = None
    current_phase_title: Optional[str] = None
    today_tasks: List[RoadmapTaskSchema]
    recommended_minutes: int
    why_it_matters: Optional[str] = None


class RoadmapProgressResponse(BaseModel):
    target_role: str
    overall_progress_percent: int
    completed_tasks_count: int
    total_tasks_count: int
    completed_phases_count: int
    total_phases_count: int
    is_outdated: bool


class TaskLearningContentResponse(BaseModel):
    """Response for GET /roadmap/tasks/{task_id}/learn — learning resources for a single task."""
    task_id: str
    title: str
    concept_explanation: str
    practice_exercise: str
    check_quiz_question: str
    check_quiz_options: List[str]
    check_quiz_answer: str
    why_it_matters: str
    task_type: str


class PracticeSuggestion(BaseModel):
    """A suggested practice topic derived from skill gaps or recent interview weak areas."""
    topic: str
    reason: str
    source: str  # "skill_gap" | "interview_weakness" | "roadmap_task"
    priority: str  # "High" | "Medium" | "Low"


class FocusSkillRequest(BaseModel):
    skill_name: str


class FocusSkillResponse(BaseModel):
    status: str  # "added" | "prioritized" | "already_focus"
    message: str
    skill_name: str
    roadmap_id: str
    task: Optional[RoadmapTaskSchema] = None

