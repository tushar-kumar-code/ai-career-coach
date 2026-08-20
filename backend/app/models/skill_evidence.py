import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class SkillEvidence(Base, TimestampMixin):
    """Model tracking individual evidence records supporting a user skill."""
    __tablename__ = "skill_evidences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)

    source = Column(String, nullable=False)  # Resume, Assessment, Project, Interview
    description = Column(Text, nullable=False)
    confidence_weight = Column(Integer, default=50, nullable=False)  # 0 to 100

    skill = relationship("Skill", backref="evidence_records")
