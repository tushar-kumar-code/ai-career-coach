import uuid
from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey
from app.core.database import Base
from app.models.base import TimestampMixin


class InterviewSession(Base, TimestampMixin):
    """Model storing adaptive mock interview sessions, questions, evaluations, and aggregated sub-scores."""
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)

    target_role = Column(String, nullable=False, default="Software Developer")
    mode = Column(String, nullable=False, default="Mixed")  # Technical, HR, Behavioral, Resume-Based, Job-Specific, Mixed
    difficulty = Column(String, nullable=False, default="Beginner")  # Beginner, Intermediate, Advanced

    question_count = Column(Integer, default=5, nullable=False)
    current_question_index = Column(Integer, default=0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    overall_score = Column(Integer, default=0, nullable=False)
    category_scores = Column(JSON, default=dict, nullable=False)  # technical, communication, problem_solving, behavioral, resume_knowledge
    readiness_status = Column(String, default="NEEDS PRACTICE", nullable=False)
    readiness_explanation = Column(String, nullable=True)

    weak_areas = Column(JSON, default=list, nullable=False)
    questions_data = Column(JSON, default=list, nullable=False)  # Array of {question_index, category, difficulty, question_text, user_answer, evaluation_json, score}

    # Backward-compatibility fields
    question_text = Column(String, nullable=True)
    user_answer_text = Column(String, nullable=True)
    star_score = Column(Integer, default=0, nullable=False)
    feedback_breakdown = Column(JSON, default=dict, nullable=False)
