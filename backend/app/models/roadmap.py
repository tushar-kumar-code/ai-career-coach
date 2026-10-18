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


class RoadmapSkillRequest(Base, TimestampMixin):
    """Pending skill ingestion request submitted from Skill Matrix, Job Engine, or Profile."""
    __tablename__ = "roadmap_skill_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    roadmap_id = Column(String, nullable=True, index=True)
    skill_name = Column(String, nullable=False)
    source = Column(String, default="Skill Matrix")  # "Skill Matrix", "Job Engine", "Profile", "Resume Analysis"
    status = Column(String, default="pending")  # "pending", "accepted", "rejected"
    priority = Column(String, default="Medium")

    # Placement recommendation details
    suggested_phase_number = Column(Integer, default=1)
    suggested_phase_title = Column(String, nullable=True)
    suggested_task_title = Column(String, nullable=True)
    placement_reason = Column(String, nullable=True)
    difficulty_level = Column(String, default="Intermediate")
    estimated_minutes = Column(Integer, default=35)
    topics_to_learn = Column(JSON, default=list)
    practice_goal = Column(String, nullable=True)
    task_payload = Column(JSON, nullable=True)

    user = relationship("User", backref="roadmap_skill_requests")
