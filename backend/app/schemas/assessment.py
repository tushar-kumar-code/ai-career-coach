from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ----------------------------------------------------
# API Request / Response Schemas
# ----------------------------------------------------

class QuestionOptionSchema(BaseModel):
    id: str
    text: str
    archetype: Optional[str] = None


class QuestionSchema(BaseModel):
    id: str
    dimension: str
    question_type: str
    question_text: str
    options: List[QuestionOptionSchema]
    order_index: int


class AssessmentSessionResponse(BaseModel):
    session_id: str
    current_step: int
    total_questions: int
    is_completed: bool
    current_question: Optional[QuestionSchema] = None
    answers_count: int


class AnswerSubmitRequest(BaseModel):
    session_id: str
    question_id: str
    selected_option_id: str


class TargetCareerSelectRequest(BaseModel):
    career_slug: str


# ----------------------------------------------------
# Gemini AI Structured Analysis Output Schemas
# ----------------------------------------------------

class SupportedStrengthSchema(BaseModel):
    strength_name: str
    evidence_reason: str


class CareerMatchSchema(BaseModel):
    slug: str
    title: str
    match_percentage: int = Field(ge=0, le=100, description="Match score percentage between 0 and 100")
    confidence_percentage: int = Field(ge=0, le=100, description="Confidence score percentage")
    why_recommended: List[str]
    supporting_strengths: List[str]
    potential_challenges: List[str]
    learning_gaps: List[str]


class CareerDiscoveryAIAnalysis(BaseModel):
    primary_archetype: str = Field(description="Career archetype e.g. Systems Builder, Data Investigator, Creative Visualizer, AI Pioneer, User Strategist")
    top_strengths: List[SupportedStrengthSchema]
    interest_profile: List[str]
    work_style_summary: str
    motivation_profile: str
    recommended_careers: List[CareerMatchSchema]
    alternative_careers: List[str]
