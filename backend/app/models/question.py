import uuid
from sqlalchemy import Column, String, Integer, JSON, Text
from app.core.database import Base
from app.models.base import TimestampMixin


class Question(Base, TimestampMixin):
    """Model for assessment questions across 12 dimensions."""
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dimension = Column(String, index=True, nullable=False)  # e.g., Logical Reasoning, Work Style
    question_type = Column(String, default="scenario")      # scenario, preference, mini_reasoning, tech_signal
    question_text = Column(Text, nullable=False)
    
    # Options array: [{ id: "A", text: "...", archetype: "...", weights: { strength: score } }]
    options = Column(JSON, nullable=False, default=list)
    difficulty_level = Column(Integer, default=1, nullable=False)  # 1 to 3
    order_index = Column(Integer, default=0, nullable=False)
