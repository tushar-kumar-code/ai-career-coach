from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    mode: str = "Mixed"  # Technical, HR, Behavioral, Resume-Based, Job-Specific, Mixed
    target_role: Optional[str] = None
    difficulty: str = "Beginner"  # Beginner, Intermediate, Advanced
    question_count: int = 5
    job_id: Optional[str] = None
    topic_focus: Optional[str] = None  # For Micro Practice: focus on a specific skill/topic


class InterviewAnswerRequest(BaseModel):
    answer_text: str = Field(..., min_length=2, description="User typed or spoken answer")


class STARAnalysis(BaseModel):
    situation_status: Optional[str] = "Good"  # Good, Needs Clarity, Missing, Not Applicable
    task_status: Optional[str] = "Good"
    action_status: Optional[str] = "Good"
    result_status: Optional[str] = "Good"
    situation_feedback: Optional[str] = None
    task_feedback: Optional[str] = None
    action_feedback: Optional[str] = None
    result_feedback: Optional[str] = None
    star_complete: bool = False
    star_score: int = 0


class InterviewEvaluationResponse(BaseModel):
    score: int
    technical_score: int
    communication_score: int
    problem_solving_score: int
    behavioral_score: int
    resume_knowledge_score: int
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    suggested_improvement: str
    ideal_answer_outline: List[str] = Field(default_factory=list)
    star_analysis: Optional[STARAnalysis] = None
    detected_weak_topic: Optional[str] = None


class InterviewQuestionSchema(BaseModel):
    question_index: int
    category: str
    difficulty: str
    question_text: str
    context_tip: Optional[str] = None
    user_answer: Optional[str] = None
    score: Optional[int] = None
    evaluation: Optional[InterviewEvaluationResponse] = None


class InterviewSessionResponse(BaseModel):
    id: str
    user_id: str
    job_id: Optional[str] = None
    topic_focus: Optional[str] = None
    target_role: str
    mode: str
    difficulty: str
    question_count: int
    current_question_index: int
    is_completed: bool
    current_question: Optional[InterviewQuestionSchema] = None
    overall_score: int = 0
    category_scores: Dict[str, int] = Field(default_factory=dict)
    readiness_status: str = "NEEDS PRACTICE"
    readiness_explanation: Optional[str] = None
    created_at: str
    updated_at: str


class InterviewFinalReportResponse(BaseModel):
    session_id: str
    target_role: str
    mode: str
    difficulty: str
    overall_score: int
    technical_score: int
    communication_score: int
    problem_solving_score: int
    behavioral_score: int
    resume_knowledge_score: int
    readiness_status: str  # EXCELLENT, READY, NEARLY READY, NEEDS PRACTICE
    readiness_explanation: str
    strong_areas: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    recommended_roadmap_topics: List[str] = Field(default_factory=list)
    questions_review: List[InterviewQuestionSchema] = Field(default_factory=list)


class InterviewReadinessResponse(BaseModel):
    overall_readiness_status: str  # EXCELLENT, READY, NEARLY READY, NEEDS PRACTICE
    average_score: int
    total_interviews_completed: int
    strongest_mode: str
    weakest_topic: Optional[str] = None
    recommendation: str


class PracticeSuggestionItem(BaseModel):
    """A suggested micro-practice topic for the student."""
    topic: str
    reason: str
    source: str  # "skill_gap" | "interview_weakness" | "roadmap_task"
    priority: str  # "High" | "Medium" | "Low"


class MicroPracticeStartResponse(BaseModel):
    """Response when kicking off a focused micro-practice session."""
    session: InterviewSessionResponse
    topic: str
    question_count: int
    message: str
