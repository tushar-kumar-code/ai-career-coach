import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey, DateTime
from app.core.database import Base
from app.models.base import TimestampMixin


class Skill(Base, TimestampMixin):
    """Model tracking individual user skills, confidence levels, and target career gaps."""
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    skill_name = Column(String, nullable=False, index=True)
    normalized_name = Column(String, nullable=False, default="", server_default="", index=True)
    category = Column(String, nullable=False, default="Technical", server_default="Technical", index=True)

    proficiency_percent = Column(Integer, default=50, nullable=False)
    proficiency_level = Column(String, default="Beginner", server_default="Beginner", nullable=False)

    confidence_score = Column(Integer, default=40, server_default="40", nullable=False)
    confidence_status = Column(String, default="Claimed", server_default="Claimed", nullable=False)

    is_verified = Column(Boolean, default=False, nullable=False)
    is_gap = Column(Boolean, default=False, nullable=False)
    
    target_required_level = Column(String, nullable=True)
    gap_status = Column(String, nullable=True, default="Matched")
    priority = Column(String, nullable=True, default="Low")
    priority_reason = Column(String, nullable=True)

    evidence_sources = Column(JSON, default=list, nullable=False)
    last_evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=True)

