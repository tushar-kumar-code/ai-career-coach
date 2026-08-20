import uuid
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from app.core.database import Base
from app.models.base import TimestampMixin


class AssessmentResponse(Base, TimestampMixin):
    """Model for recording user session, answers, and AI discovery results."""
    __tablename__ = "assessment_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String, default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, COMPLETED
    current_step = Column(Integer, default=1, nullable=False)
    
    # Map of question_id -> { option_id, option_text, dimension, weights }
    dimension_answers = Column(JSON, nullable=False, default=dict)
    
    # AI generated archetype & career role matches
    computed_archetype = Column(String, nullable=True)
    role_recommendations = Column(JSON, nullable=False, default=list)
    ai_analysis_json = Column(JSON, nullable=True, default=dict)
    
    selected_target_career = Column(String, nullable=True)
