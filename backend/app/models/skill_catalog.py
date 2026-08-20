import uuid
from sqlalchemy import Column, String, Text
from app.core.database import Base
from app.models.base import TimestampMixin


class SkillDefinition(Base, TimestampMixin):
    """Structured catalog taxonomy of skills and categories."""
    __tablename__ = "skill_definitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)  # Programming Languages, Web Development, Databases, etc.
    description = Column(Text, nullable=True)
