from typing import List, Optional
from pydantic import BaseModel, Field


class RoadmapTaskSchema(BaseModel):
    id: str
    title: str
    skill: str
    estimated_minutes: int = 30
    why_matters: str
    practice_activity: str
    completed: bool = False
    completed_at: Optional[str] = None


class RoadmapProjectSchema(BaseModel):
    id: str
    title: str
    objective: str
    skills_practiced: List[str] = Field(default_factory=list)
    difficulty: str = "Intermediate"
    expected_outcome: str
    resume_relevance: str
    completed: bool = False


class RoadmapMilestoneSchema(BaseModel):
    id: str
    title: str
    criteria: str
    completed: bool = False


class RoadmapSkillItem(BaseModel):
    name: str
    status: str = "Missing"  # Verified, Supported, Missing
    priority: str = "Essential"  # Essential, Core, Optional
    level: str = "Beginner"


class RoadmapPhaseSchema(BaseModel):
    phase_id: str
    name: str
    description: str
    estimated_weeks: int = 2
    skills: List[RoadmapSkillItem] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    tasks: List[RoadmapTaskSchema] = Field(default_factory=list)
    projects: List[RoadmapProjectSchema] = Field(default_factory=list)
    milestones: List[RoadmapMilestoneSchema] = Field(default_factory=list)


class RoadmapGenerateRequest(BaseModel):
    user_level: Optional[str] = "Beginner"
    hours_per_day: Optional[int] = 1
    days_per_week: Optional[int] = 5
    preferred_learning_style: Optional[str] = "Hands-on"
    target_career_id: Optional[str] = None


class RoadmapPreferencesRequest(BaseModel):
    hours_per_day: int = Field(ge=1, le=12)
    days_per_week: int = Field(ge=1, le=7)
    preferred_learning_style: str = "Hands-on"
    user_level: str = "Beginner"


class DailyTasksResponse(BaseModel):
    roadmap_id: str
    target_role: str
    current_phase_name: str
    hours_budget: float
    today_focus_title: str
    why_it_matters: str
    tasks: List[RoadmapTaskSchema]


class RoadmapProgressResponse(BaseModel):
    roadmap_id: str
    target_role: str
    overall_progress_percent: int
    completed_tasks_count: int
    total_tasks_count: int
    completed_projects_count: int
    total_projects_count: int
    completed_milestones_count: int
    total_milestones_count: int
    is_outdated: bool


class RoadmapDetailResponse(BaseModel):
    id: str
    user_id: str
    target_career_id: Optional[str] = None
    target_role: str
    user_level: str
    overall_progress_percent: int
    is_active: bool
    is_outdated: bool
    hours_per_day: int
    days_per_week: int
    preferred_learning_style: str
    total_estimated_weeks: int
    phases: List[RoadmapPhaseSchema]
    completed_task_ids: List[str] = Field(default_factory=list)
    completed_milestone_ids: List[str] = Field(default_factory=list)
    completed_project_ids: List[str] = Field(default_factory=list)


class FocusSkillRequest(BaseModel):
    skill_name: str


class FocusSkillResponse(BaseModel):
    status: str  # "added", "prioritized", "already_focus"
    message: str
    skill_name: str
    roadmap_id: str
    task: Optional[RoadmapTaskSchema] = None
