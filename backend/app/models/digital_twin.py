import uuid
import datetime
from sqlalchemy import Column, String, Integer, JSON, Date, Boolean, ForeignKey, DateTime, Text
from app.core.database import Base
from app.models.base import TimestampMixin


class CareerDigitalTwin(Base, TimestampMixin):
    """
    Per-user Career Digital Twin -- stores the computed readiness state.
    Upserted (at most once per day) from live module data.
    Never stores hardcoded values: all fields computed from real evidence.
    """
    __tablename__ = "career_digital_twins"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Overall composite score 0-100 (weighted formula in readiness_engine.py)
    overall_readiness_score = Column(Integer, default=0, nullable=False)
    readiness_label = Column(String, default="Not Started", nullable=False)

    # Sub-scores each 0-100
    skill_readiness = Column(Integer, default=0, nullable=False)
    resume_readiness = Column(Integer, default=0, nullable=False)
    interview_readiness = Column(Integer, default=0, nullable=False)
    roadmap_progress = Column(Integer, default=0, nullable=False)
    job_match_readiness = Column(Integer, default=0, nullable=False)
    portfolio_readiness = Column(Integer, default=0, nullable=False)

    # Evidence metadata
    target_career = Column(String, nullable=True)
    primary_archetype = Column(String, nullable=True)
    experience_level = Column(String, default="Beginner", nullable=False)

    # Derived gap and strength summaries
    top_strengths = Column(JSON, default=list, nullable=False)
    priority_gaps = Column(JSON, default=list, nullable=False)
    critical_missing_skills = Column(JSON, default=list, nullable=False)

    # Next Best Action
    next_action = Column(JSON, default=dict, nullable=False)

    # Evidence counts used for computing scores
    evidence_summary = Column(JSON, default=dict, nullable=False)

    last_computed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    snapshot_date = Column(Date, default=datetime.date.today, nullable=False)


class ReadinessSnapshot(Base, TimestampMixin):
    """Historical readiness score snapshot -- one row per user per day for trend charts."""
    __tablename__ = "readiness_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, default=datetime.date.today, nullable=False, index=True)

    overall_readiness_score = Column(Integer, default=0, nullable=False)
    skill_readiness = Column(Integer, default=0, nullable=False)
    resume_readiness = Column(Integer, default=0, nullable=False)
    interview_readiness = Column(Integer, default=0, nullable=False)
    roadmap_progress = Column(Integer, default=0, nullable=False)
    job_match_readiness = Column(Integer, default=0, nullable=False)
    portfolio_readiness = Column(Integer, default=0, nullable=False)


class UserAchievement(Base, TimestampMixin):
    """Earned achievements -- only created when real DB evidence is found. Never fabricated."""
    __tablename__ = "user_achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    achievement_key = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String, default="trophy", nullable=False)
    category = Column(String, default="General", nullable=False)
    evidence_description = Column(String, nullable=True)
    earned_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
