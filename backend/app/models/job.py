import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, JSON, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Job(Base, TimestampMixin):
    """Model storing job postings from catalog or external job search providers."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, nullable=True, index=True)
    provider_name = Column(String, default="catalog", nullable=False, index=True)

    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String, default="Remote", nullable=False, index=True)
    is_remote = Column(Boolean, default=True, nullable=False)
    employment_type = Column(String, default="Full-time", nullable=False)
    experience_level = Column(String, default="Mid Level", nullable=False)

    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list, nullable=False)
    preferred_skills = Column(JSON, default=list, nullable=False)
    education_requirements = Column(String, default="Bachelor's degree or equivalent experience", nullable=False)

    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String, default="USD", nullable=False)

    source_url = Column(String, nullable=True)
    posted_date = Column(String, nullable=True)


class SavedJob(Base, TimestampMixin):
    """Model storing user bookmarked/saved jobs."""
    __tablename__ = "saved_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    notes = Column(Text, nullable=True)
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job", backref="saved_by_users")
    user = relationship("User", backref="saved_jobs")


class JobApplication(Base, TimestampMixin):
    """Model tracking user job application status lifecycle."""
    __tablename__ = "job_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status: Saved, Applied, Assessment, Interview, Offer, Rejected, Withdrawn
    status = Column(String, default="Applied", nullable=False, index=True)
    applied_date = Column(String, nullable=True)
    interview_date = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)

    job = relationship("Job", backref="applications")
    user = relationship("User", backref="job_applications")
    status_history = relationship("ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan")


class ApplicationStatusHistory(Base, TimestampMixin):
    """Audit log tracking history of status transitions for an application."""
    __tablename__ = "application_status_histories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String, ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True)

    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)

    application = relationship("JobApplication", back_populates="status_history")
