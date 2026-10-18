from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ParsedContactInfo(BaseModel):
    name: str = "Candidate"
    email: str = ""
    phone: str = ""
    location: str = ""
    headline: str = ""
    summary: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class ResumeExperienceItem(BaseModel):
    role: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    description: str = ""
    key_achievements: List[str] = Field(default_factory=list)


class ResumeProjectItem(BaseModel):
    title: str = ""
    role: str = ""
    technologies: List[str] = Field(default_factory=list)
    description: str = ""
    link: str = ""


class ResumeEducationItem(BaseModel):
    degree: str = ""
    institution: str = ""
    field_of_study: str = ""
    start_year: str = ""
    end_year: str = ""
    grade: str = ""


class ResumeCertificationItem(BaseModel):
    name: str = ""
    issuer: str = ""
    issue_date: str = ""
    credential_id_or_url: str = ""


class ResumeSkillItem(BaseModel):
    name: str
    category: str = "Technical"
    proficiency_estimated: Optional[int] = Field(default=None, ge=0, le=100)


class ResumeAchievementItem(BaseModel):
    title: str = ""
    issuer_or_event: str = ""
    year: str = ""
    description: str = ""


class ResumePublicationItem(BaseModel):
    title: str = ""
    authors_or_journal: str = ""
    date_or_year: str = ""
    url_or_doi: str = ""
    description: str = ""


class ResumeLanguageItem(BaseModel):
    language: str = ""
    proficiency: str = ""  # Native, Fluent, Professional, Intermediate, Elementary


class ResumeExtracurricularItem(BaseModel):
    role: str = ""
    organization: str = ""
    duration: str = ""
    description: str = ""


class ResumeVerificationAndProfileExtraction(BaseModel):
    is_resume: bool = Field(
        ...,
        description="True ONLY if the text is a genuine candidate resume or curriculum vitae (CV). False for invoices, bills, receipts, homework, general articles, or non-resume documents."
    )
    confidence_score: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Confidence that the document is genuinely a resume (0-100)."
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="If is_resume is False, reason explaining why this document is not a resume."
    )
    about_user: ParsedContactInfo = Field(default_factory=ParsedContactInfo)
    skills: List[ResumeSkillItem] = Field(default_factory=list)
    experience: List[ResumeExperienceItem] = Field(default_factory=list)
    projects: List[ResumeProjectItem] = Field(default_factory=list)
    education: List[ResumeEducationItem] = Field(default_factory=list)
    certifications: List[ResumeCertificationItem] = Field(default_factory=list)
    achievements: List[ResumeAchievementItem] = Field(default_factory=list)
    publications: List[ResumePublicationItem] = Field(default_factory=list)
    languages: List[ResumeLanguageItem] = Field(default_factory=list)
    extracurriculars: List[ResumeExtracurricularItem] = Field(default_factory=list)


class ExtractedSkillSchema(BaseModel):
    name: str
    category: str = "Technical"
    proficiency_estimated: Optional[int] = Field(default=None, ge=0, le=100)
    source: str = "Resume Extraction"
    confidence_level: str = "Medium"  # High, Medium, Low


class ScoringFactorItem(BaseModel):
    factor_name: str
    weight: int  # e.g. 35, 20, 15, 10
    factor_score: int  # 0 to 100
    weighted_contribution: float  # factor_score * weight / 100
    description: str
    strengths: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    status: str = "evaluated"  # evaluated, unverifiable, omitted


class EligibilityItem(BaseModel):
    criterion: str
    status: str  # MET, NOT_MET, UNKNOWN
    details: str


class ATSBreakdownSchema(BaseModel):
    overall_ats_score: int = Field(ge=0, le=100)
    formatting_score: int = Field(ge=0, le=100)
    keyword_score: int = Field(ge=0, le=100)
    skills_score: int = Field(ge=0, le=100)
    experience_score: int = Field(ge=0, le=100)
    readability_score: int = Field(ge=0, le=100)
    # Mode details & transparent mathematical breakdown
    scoring_mode: str = "general"  # target_role | job_description | general
    mode_label: str = "General Resume Quality & ATS Readiness"
    target_context: Optional[str] = None
    factors: List[ScoringFactorItem] = Field(default_factory=list)
    eligibility_criteria: List[EligibilityItem] = Field(default_factory=list)
    preferred_skills_matching: List[str] = Field(default_factory=list)
    preferred_skills_missing: List[str] = Field(default_factory=list)
    missing_data_notes: List[str] = Field(default_factory=list)
    is_fresher_mode: bool = False


class TargetCareerMatchSchema(BaseModel):
    target_career_name: str
    match_percentage: int = Field(ge=0, le=100)
    matching_skills: List[str]
    missing_skills: List[str]
    experience_alignment: str
    recommendation: str
    match_source: str = "catalog"  # catalog | job_description | none
    preferred_skills_matching: List[str] = Field(default_factory=list)
    preferred_skills_missing: List[str] = Field(default_factory=list)


class BulletImprovementSchema(BaseModel):
    original_text: str
    improved_text: str
    explanation: str


class ResumeDomainSuggestion(BaseModel):
    domain_name: str
    match_percentage: int = Field(ge=0, le=100)
    fit_reason: str
    matched_skills: List[str] = Field(default_factory=list)
    recommended_roles: List[str] = Field(default_factory=list)
    growth_areas: List[str] = Field(default_factory=list)
    category: str = "Technology"


class JobDescriptionMatchRequest(BaseModel):
    job_description: str = Field(..., min_length=20, max_length=15000, description="Pasted job description text")


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
    formatted_text: Optional[str] = None
    raw_text: Optional[str] = None
    # Rich Candidate Profile Extracted from Resume
    about_user: Optional[ParsedContactInfo] = None
    experience: List[ResumeExperienceItem] = Field(default_factory=list)
    projects: List[ResumeProjectItem] = Field(default_factory=list)
    education: List[ResumeEducationItem] = Field(default_factory=list)
    certifications: List[ResumeCertificationItem] = Field(default_factory=list)
    achievements: List[ResumeAchievementItem] = Field(default_factory=list)
    publications: List[ResumePublicationItem] = Field(default_factory=list)
    languages: List[ResumeLanguageItem] = Field(default_factory=list)
    extracurriculars: List[ResumeExtracurricularItem] = Field(default_factory=list)
    # Mode & context
    scoring_mode: str = "general"  # target_role | job_description | general
    job_description_snippet: Optional[str] = None
    recommended_career_paths: List[str] = Field(default_factory=list)
    suggested_domains: List[ResumeDomainSuggestion] = Field(default_factory=list)

