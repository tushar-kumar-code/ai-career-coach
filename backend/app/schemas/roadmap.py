from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RoadmapGenerateRequest(BaseModel):
    user_level: Optional[str] = Field(default="Beginner", description="Beginner (Scratch), Intermediate, or Advanced")
    hours_per_day: int = Field(default=1, ge=1, le=8, description="Available study hours per day")
    days_per_week: int = Field(default=5, ge=1, le=7, description="Available study days per week")
    preferred_learning_style: str = Field(default="Hands-on", description="Hands-on, Visual, or Reading")
    career_goal: Optional[str] = Field(default="Entry-level Job", description="Internship, Entry-level Job, Career Transition, Certification, or Skill Mastery")
    target_role: Optional[str] = Field(default=None, description="Explicit target role or domain override")
    track_pace: Optional[str] = Field(default="Standard", description="Express (3 Levels), Standard (4-5 Levels), or Comprehensive (6-7 Levels)")
    target_phases_count: Optional[int] = Field(default=None, ge=2, le=9, description="Custom number of levels")
    domain_requirement: Optional[str] = Field(default=None, description="Custom domain focus or special requirement")


class RoadmapPreferencesRequest(BaseModel):
    user_level: Optional[str] = Field(default="Beginner", description="Beginner (Scratch), Intermediate, or Advanced")
    hours_per_day: int = Field(..., ge=1, le=8)
    days_per_week: int = Field(..., ge=1, le=7)
    preferred_learning_style: str = Field(...)
    career_goal: Optional[str] = Field(default="Entry-level Job", description="Internship, Entry-level Job, Career Transition, Certification, or Skill Mastery")
    target_role: Optional[str] = Field(default=None, description="Target career domain (e.g. DevOps, Data Science, Full Stack)")
    track_pace: Optional[str] = Field(default="Standard", description="Express, Standard, Comprehensive, or Dynamic")
    target_phases_count: Optional[int] = Field(default=None, ge=2, le=9, description="Custom flexible number of levels")
    domain_requirement: Optional[str] = Field(default=None, description="Custom focus or specific domain requirements")


class CustomPhaseRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Custom level/milestone title")
    description: Optional[str] = Field(default="Custom user milestone tailored to specific learning goals.")
    topics: Optional[List[str]] = Field(default_factory=list, description="List of subtopics or skills to cover")
    estimated_minutes: Optional[int] = Field(default=60, ge=15, le=300)


class RoadmapTaskSchema(BaseModel):
    id: str
    title: str
    description: str
    estimated_minutes: int
    task_type: str
    why_it_matters: str
    is_completed: bool
    completed_at: Optional[str] = None
    # Topic-wise syllabus & guidance fields (tells user WHAT to learn)
    topics_to_learn: Optional[List[str]] = Field(default_factory=list, description="Exhaustive list of specific subtopics/concepts to learn")
    learning_focus: Optional[str] = Field(default=None, description="Key advice on what to prioritize during study")
    practice_goal: Optional[str] = Field(default=None, description="Concrete coding or hands-on practice exercise")
    recommended_resources: Optional[List[str]] = Field(default_factory=list, description="Recommended standard docs or study topics")
    difficulty_level: Optional[str] = Field(default="Beginner", description="Scratch, Beginner, Intermediate, or Advanced")
    prerequisites: Optional[List[str]] = Field(default_factory=list, description="Prerequisite concepts")
    # Learning resource fields (Phase 3 legacy support)
    concept_explanation: Optional[str] = None
    practice_exercise: Optional[str] = None
    check_quiz_question: Optional[str] = None
    check_quiz_options: Optional[List[str]] = None
    check_quiz_answer: Optional[str] = None
    # Priority flag from Interview feedback loop
    is_priority: Optional[bool] = False
    priority_reason: Optional[str] = None
    skill: Optional[str] = None
    # Actionable outcome & verification fields
    expected_outcome: Optional[str] = Field(default=None, description="Concrete deliverable or output produced")
    verification_method: Optional[str] = Field(default=None, description="How understanding or completion is verified")
    next_step: Optional[str] = Field(default=None, description="Clear next step after completing this task")


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
    # Level progression & test fields
    level_name: Optional[str] = None
    level_theme: Optional[str] = None
    level_icon: Optional[str] = None
    is_unlocked: Optional[bool] = True
    test_passed: Optional[bool] = False
    test_score: Optional[int] = None
    stars: Optional[int] = 0
    xp_reward: Optional[int] = 100


class RoadmapResponse(BaseModel):
    id: str
    user_id: str
    target_role: str
    user_level: Optional[str] = "Beginner"
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
    passed_level_ids: Optional[List[str]] = Field(default_factory=list)
    current_unlocked_level: Optional[int] = 1
    total_xp: Optional[int] = 0
    adventurer_level: Optional[int] = 1
    career_goal: Optional[str] = "Entry-level Job"
    schedule_notes: Optional[str] = None
    total_estimated_minutes: Optional[int] = None
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
    is_level_test_recommended: bool = False
    next_step: Optional[str] = None
    completion_status: Optional[str] = "in_progress"
    learner_level: Optional[str] = "Beginner"
    starting_point_note: Optional[str] = None
    career_goal: Optional[str] = None


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


# ----------------------------------------------------
# Level Test & Progression Schemas
# ----------------------------------------------------

class LevelTestQuestion(BaseModel):
    id: str
    question: str
    topic: str
    options: List[str]
    correct_answer: str
    explanation: str
    code_snippet: Optional[str] = None
    difficulty: Optional[str] = "Intermediate"
    question_type: Optional[str] = "conceptual"


class LevelTestResponse(BaseModel):
    phase_id: str
    phase_number: int
    phase_title: str
    level_name: str
    target_career: str
    passing_score_percent: int = 70
    xp_reward: int = 100
    questions: List[LevelTestQuestion]


class LevelTestSubmitRequest(BaseModel):
    answers: Dict[str, str]  # question_id -> selected_option


class QuestionResultDetail(BaseModel):
    question_id: str
    question: str
    topic: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    code_snippet: Optional[str] = None


class LevelTestSubmitResponse(BaseModel):
    phase_id: str
    phase_number: int
    level_name: str
    score_percent: int
    passed: bool
    passing_score_percent: int = 70
    correct_count: int
    total_questions: int
    stars_awarded: int = 0
    xp_earned: int = 0
    mastery_level: str = "Mastered"
    next_level_unlocked: bool
    unlocked_phase_id: Optional[str] = None
    unlocked_level_name: Optional[str] = None
    feedback: str
    missed_topics: List[str] = Field(default_factory=list)
    results_detail: List[QuestionResultDetail] = Field(default_factory=list)
    recovery_recommendations: List[str] = Field(default_factory=list, description="Targeted recovery and revision instructions for missed topics")
    guided_practice_exercise: Optional[str] = Field(default=None, description="Guided practice drill to reinforce weak concepts before retrying")
    can_retry: bool = True


class CreateRoadmapSkillRequestSchema(BaseModel):
    skill_name: str
    source: Optional[str] = "Skill Matrix"
    priority: Optional[str] = "Medium"


class AcceptRoadmapSkillRequestSchema(BaseModel):
    target_phase_number: Optional[int] = None


class RoadmapSkillRequestResponse(BaseModel):
    id: str
    user_id: str
    roadmap_id: Optional[str] = None
    skill_name: str
    source: str
    status: str
    priority: str
    suggested_phase_number: int
    suggested_phase_title: Optional[str] = None
    suggested_task_title: Optional[str] = None
    placement_reason: Optional[str] = None
    difficulty_level: str
    estimated_minutes: int
    topics_to_learn: List[str] = Field(default_factory=list)
    practice_goal: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoadmapAssistantRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or query about roadmap")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Prior conversation messages")
    current_phase_id: Optional[str] = Field(default=None, description="Active level/phase ID")
    current_task_id: Optional[str] = Field(default=None, description="Active task/topic ID")


class RoadmapAssistantResponse(BaseModel):
    response: str
    provider: str = "Groq AI"
    suggested_actions: Optional[List[str]] = Field(default_factory=list)

