import datetime
from sqlalchemy import Column, DateTime
from app.core.database import Base


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps to models."""
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )
