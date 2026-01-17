"""Lesson model."""

from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
import uuid
import enum


class LessonStatus(str, enum.Enum):
    """Lesson processing status."""
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    TRANSCRIBING = "TRANSCRIBING"
    EXTRACTING = "EXTRACTING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Lesson(Base):
    """Lesson table."""

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    lesson_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(20), default=LessonStatus.CREATED.value)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    audio_url: Mapped[str] = mapped_column(String(500), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    extraction: Mapped[dict] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="lessons")
    student: Mapped["Student"] = relationship("Student", back_populates="lessons")
    outputs: Mapped[list["Output"]] = relationship("Output", back_populates="lesson", cascade="all, delete-orphan")
