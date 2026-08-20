import uuid
from sqlalchemy import Column, String, Integer, JSON, Text, ForeignKey
from app.core.database import Base
from app.models.base import TimestampMixin


class Resume(Base, TimestampMixin):
    """Model storing uploaded user resume content, parsed JSON signals, ATS evaluation, and target match."""
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    
    # Real Calculated ATS Sub-scores
    overall_ats_score = Column(Integer, default=0, nullable=False)
    formatting_score = Column(Integer, default=0, nullable=False)
    keyword_score = Column(Integer, default=0, nullable=False)
    skills_score = Column(Integer, default=0, nullable=False)
    experience_score = Column(Integer, default=0, nullable=False)
    readability_score = Column(Integer, default=0, nullable=False)
    
    # Target Career Matching
    target_career_name = Column(String, nullable=True)
    target_match_percentage = Column(Integer, default=0, nullable=False)
    matching_skills = Column(JSON, default=list, nullable=False)
    missing_skills = Column(JSON, default=list, nullable=False)
    
    # Detailed Analysis JSON Structures
    ats_breakdown_json = Column(JSON, default=dict, nullable=False)
    formatting_risk_flags = Column(JSON, default=list, nullable=False)
    parsed_contact_info = Column(JSON, default=dict, nullable=False)
    parsed_skills = Column(JSON, default=list, nullable=False)
    parsed_experience = Column(JSON, default=list, nullable=False)
    parsed_education = Column(JSON, default=list, nullable=False)
    parsed_projects = Column(JSON, default=list, nullable=False)
    improvement_suggestions = Column(JSON, default=list, nullable=False)
