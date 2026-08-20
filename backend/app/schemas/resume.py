from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ParsedContactInfo(BaseModel):
    name: str = "Candidate"
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class ExtractedSkillSchema(BaseModel):
    name: str
    category: str = "Technical"
    proficiency_estimated: int = Field(default=70, ge=0, le=100)
    source: str = "Resume Extraction"
    confidence_level: str = "Medium"  # High, Medium, Low


class ATSBreakdownSchema(BaseModel):
    overall_ats_score: int = Field(ge=0, le=100)
    formatting_score: int = Field(ge=0, le=100)
    keyword_score: int = Field(ge=0, le=100)
    skills_score: int = Field(ge=0, le=100)
    experience_score: int = Field(ge=0, le=100)
    readability_score: int = Field(ge=0, le=100)


class TargetCareerMatchSchema(BaseModel):
    target_career_name: str
    match_percentage: int = Field(ge=0, le=100)
    matching_skills: List[str]
    missing_skills: List[str]
    experience_alignment: str
    recommendation: str


class BulletImprovementSchema(BaseModel):
    original_text: str
    improved_text: str
    explanation: str


class ResumeAnalysisResponse(BaseModel):
    id: str
    filename: str
    ats_score: int
    ats_breakdown: ATSBreakdownSchema
    target_match: TargetCareerMatchSchema
    contact_info: ParsedContactInfo
    extracted_skills: List[ExtractedSkillSchema]
    formatting_risk_flags: List[str]
    improvement_suggestions: List[BulletImprovementSchema]
