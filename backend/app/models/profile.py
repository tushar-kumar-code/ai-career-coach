import uuid
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class UserProfile(Base, TimestampMixin):
    """Career Digital Twin Profile model storing overall metrics, archetype, and verified skills."""
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    target_career = Column(String, nullable=True, default="Software Developer")
    primary_archetype = Column(String, nullable=True, default="Systems Builder")
    job_readiness_score = Column(Integer, default=50, nullable=False)
    
    # JSON structure storing evidence-backed verified skills & gaps
    skills_matrix = Column(JSON, default=dict, nullable=False)
    recommended_roles = Column(JSON, default=list, nullable=False)
    evidence_points = Column(JSON, default=list, nullable=False)

    user = relationship("User", backref="profile")
