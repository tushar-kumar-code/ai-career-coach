import uuid
from sqlalchemy import Column, String, Integer, JSON, Text
from app.core.database import Base
from app.models.base import TimestampMixin


class CareerRole(Base, TimestampMixin):
    """Structured catalog of career roles with requirements, difficulty, and metadata."""
    __tablename__ = "career_roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    difficulty_level = Column(String, default="Intermediate")  # Entry, Intermediate, Advanced
    
    # Metadata JSON fields
    required_skills = Column(JSON, default=list, nullable=False)
    important_skills = Column(JSON, default=list, nullable=False)
    optional_skills = Column(JSON, default=list, nullable=False)
    recommended_proficiency = Column(JSON, default=dict, nullable=False)
    preferred_strengths = Column(JSON, default=list, nullable=False)
    interest_areas = Column(JSON, default=list, nullable=False)
    work_style = Column(String, nullable=True)
    responsibilities = Column(JSON, default=list, nullable=False)
    learning_areas = Column(JSON, default=list, nullable=False)

