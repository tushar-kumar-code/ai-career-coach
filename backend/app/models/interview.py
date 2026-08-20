import uuid
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from app.core.database import Base
from app.models.base import TimestampMixin


class InterviewSession(Base, TimestampMixin):
    """Model storing STAR method mock interview sessions and AI scoring breakdowns."""
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    target_role = Column(String, nullable=False)
    question_text = Column(String, nullable=False)
    user_answer_text = Column(String, nullable=True)
    
    star_score = Column(Integer, default=0, nullable=False)
    feedback_breakdown = Column(JSON, default=dict, nullable=False)
