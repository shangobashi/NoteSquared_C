"""Output model."""

from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
import uuid
import enum


class OutputType(str, enum.Enum):
    """Output types."""
    STUDENT_RECAP = "STUDENT_RECAP"
    PRACTICE_PLAN = "PRACTICE_PLAN"
    PARENT_EMAIL = "PARENT_EMAIL"


class Output(Base):
    """Output table - generated content from lessons."""

    __tablename__ = "outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id"), nullable=False, index=True)
    output_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    original_content: Mapped[str] = mapped_column(Text, nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="outputs")
