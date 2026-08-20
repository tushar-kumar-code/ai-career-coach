import uuid
from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Roadmap(Base, TimestampMixin):
    """Model storing personalized learning roadmaps, phases, daily focus tasks, and project progress."""
    __tablename__ = "roadmaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    target_career_id = Column(String, nullable=True)
    target_role = Column(String, nullable=False, index=True)
    user_level = Column(String, default="Beginner", nullable=False)
    overall_progress_percent = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_outdated = Column(Boolean, default=False, nullable=False)

    hours_per_day = Column(Integer, default=1, nullable=False)
    days_per_week = Column(Integer, default=5, nullable=False)
    preferred_learning_style = Column(String, default="Hands-on", nullable=False)
    total_estimated_weeks = Column(Integer, default=8, nullable=False)

    # JSON structures for roadmap phases, tasks, projects, milestones
    phases = Column(JSON, default=list, nullable=False)
    completed_task_ids = Column(JSON, default=list, nullable=False)
    completed_milestone_ids = Column(JSON, default=list, nullable=False)
    completed_project_ids = Column(JSON, default=list, nullable=False)

    user = relationship("User", backref="roadmaps")
