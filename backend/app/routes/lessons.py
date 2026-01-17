"""Lesson management routes."""

import os
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import os

from ..database import get_db
from ..models.user import User
from ..models.student import Student
from ..models.lesson import Lesson, LessonStatus
from ..models.output import Output, OutputType
from ..auth import get_current_user
from ..services.ai_pipeline import process_lesson_pipeline
from ..config import get_settings

router = APIRouter(prefix="/lessons", tags=["lessons"])
settings = get_settings()


def _upload_to_blob(local_path: str, blob_path: str) -> str | None:
    """Upload a local file to Vercel Blob and return the public URL."""
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not token:
        return None
    try:
        from vercel import blob
    except Exception:
        return None

    uploaded = blob.upload_file(
        local_path=local_path,
        path=blob_path,
        access="public",
    )
    for key in ("url", "download_url", "downloadUrl"):
        if hasattr(uploaded, key):
            return getattr(uploaded, key)
        if isinstance(uploaded, dict) and key in uploaded:
            return uploaded[key]
    return None


class LessonCreate(BaseModel):
    """Create lesson request."""
    student_id: str
    lesson_date: date | None = None


class LessonResponse(BaseModel):
    """Lesson response."""
    id: str
    student_id: str
    student_name: str
    lesson_date: str
    status: str
    duration_seconds: int | None
    error_message: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class LessonDetailResponse(LessonResponse):
    """Detailed lesson response with outputs."""
    transcript: str | None = None
    outputs: list["OutputResponse"] = []


class OutputResponse(BaseModel):
    """Output response."""
    id: str
    output_type: str
    content: str
    is_edited: bool
    is_shared: bool
    created_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    request: LessonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new lesson."""
    # Verify student exists and belongs to user
    result = await db.execute(
        select(Student).where(
            Student.id == request.student_id,
            Student.owner_id == current_user.id,
        )
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    lesson = Lesson(
        owner_id=current_user.id,
        student_id=request.student_id,
        lesson_date=request.lesson_date or date.today(),
        status=LessonStatus.CREATED.value,
    )
    db.add(lesson)
    await db.flush()
    await db.refresh(lesson)

    return LessonResponse(
        id=lesson.id,
        student_id=lesson.student_id,
        student_name=student.full_name,
        lesson_date=lesson.lesson_date.isoformat(),
        status=lesson.status,
        duration_seconds=lesson.duration_seconds,
        error_message=lesson.error_message,
        created_at=lesson.created_at.isoformat(),
        updated_at=lesson.updated_at.isoformat(),
    )


@router.post("/{lesson_id}/upload", response_model=LessonResponse)
async def upload_audio(
    lesson_id: str,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload audio file for a lesson and start processing."""
    # Get lesson
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.student))
        .where(
            Lesson.id == lesson_id,
            Lesson.owner_id == current_user.id,
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    # Validate file type
    allowed_types = ["audio/m4a", "audio/mp3", "audio/mpeg", "audio/wav", "audio/webm", "audio/mp4"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format. Allowed: m4a, mp3, wav, webm",
        )

    # Save audio file to a temp location for processing and optional blob upload
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_extension = audio.filename.split(".")[-1] if audio.filename else "m4a"
    file_name = f"{lesson_id}_{uuid.uuid4()}.{file_extension}"
    local_path = os.path.join(settings.upload_dir, file_name)

    content = await audio.read()
    with open(local_path, "wb") as f:
        f.write(content)

    blob_url = _upload_to_blob(local_path, f"lessons/{lesson_id}/{file_name}")
    file_path = blob_url or local_path
    if blob_url:
        try:
            os.remove(local_path)
        except OSError:
            pass

    # Update lesson
    lesson.audio_url = file_path
    lesson.status = LessonStatus.UPLOADED.value
    await db.flush()
    await db.refresh(lesson)

    # Start background processing
    background_tasks.add_task(
        process_lesson_pipeline,
        lesson_id=lesson.id,
        student_name=lesson.student.full_name,
        instrument=lesson.student.instrument,
    )

    return LessonResponse(
        id=lesson.id,
        student_id=lesson.student_id,
        student_name=lesson.student.full_name,
        lesson_date=lesson.lesson_date.isoformat(),
        status=lesson.status,
        duration_seconds=lesson.duration_seconds,
        error_message=lesson.error_message,
        created_at=lesson.created_at.isoformat(),
        updated_at=lesson.updated_at.isoformat(),
    )


@router.get("", response_model=list[LessonResponse])
async def list_lessons(
    student_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all lessons, optionally filtered by student."""
    query = (
        select(Lesson)
        .options(selectinload(Lesson.student))
        .where(Lesson.owner_id == current_user.id)
    )

    if student_id:
        query = query.where(Lesson.student_id == student_id)

    query = query.order_by(Lesson.lesson_date.desc())

    result = await db.execute(query)
    lessons = result.scalars().all()

    return [
        LessonResponse(
            id=l.id,
            student_id=l.student_id,
            student_name=l.student.full_name if l.student else "Unknown",
            lesson_date=l.lesson_date.isoformat(),
            status=l.status,
            duration_seconds=l.duration_seconds,
            error_message=l.error_message,
            created_at=l.created_at.isoformat(),
            updated_at=l.updated_at.isoformat(),
        )
        for l in lessons
    ]


@router.get("/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a lesson with outputs."""
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.student), selectinload(Lesson.outputs))
        .where(
            Lesson.id == lesson_id,
            Lesson.owner_id == current_user.id,
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    return LessonDetailResponse(
        id=lesson.id,
        student_id=lesson.student_id,
        student_name=lesson.student.full_name if lesson.student else "Unknown",
        lesson_date=lesson.lesson_date.isoformat(),
        status=lesson.status,
        duration_seconds=lesson.duration_seconds,
        error_message=lesson.error_message,
        created_at=lesson.created_at.isoformat(),
        updated_at=lesson.updated_at.isoformat(),
        transcript=lesson.transcript,
        outputs=[
            OutputResponse(
                id=o.id,
                output_type=o.output_type,
                content=o.content,
                is_edited=o.is_edited,
                is_shared=o.is_shared,
                created_at=o.created_at.isoformat(),
            )
            for o in sorted(lesson.outputs, key=lambda x: ["STUDENT_RECAP", "PRACTICE_PLAN", "PARENT_EMAIL"].index(x.output_type) if x.output_type in ["STUDENT_RECAP", "PRACTICE_PLAN", "PARENT_EMAIL"] else 99)
        ],
    )


@router.get("/{lesson_id}/status")
async def get_lesson_status(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get lesson processing status (for polling)."""
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == lesson_id,
            Lesson.owner_id == current_user.id,
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    return {
        "id": lesson.id,
        "status": lesson.status,
        "error_message": lesson.error_message,
    }


@router.post("/{lesson_id}/process", response_model=LessonResponse)
async def process_lesson(
    lesson_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry processing a failed lesson."""
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.student))
        .where(
            Lesson.id == lesson_id,
            Lesson.owner_id == current_user.id,
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    if lesson.status not in [LessonStatus.FAILED.value, LessonStatus.UPLOADED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson cannot be reprocessed",
        )

    # Reset status
    lesson.status = LessonStatus.UPLOADED.value
    lesson.error_message = None
    await db.flush()

    # Start background processing
    background_tasks.add_task(
        process_lesson_pipeline,
        lesson_id=lesson.id,
        student_name=lesson.student.full_name,
        instrument=lesson.student.instrument,
    )

    return LessonResponse(
        id=lesson.id,
        student_id=lesson.student_id,
        student_name=lesson.student.full_name,
        lesson_date=lesson.lesson_date.isoformat(),
        status=lesson.status,
        duration_seconds=lesson.duration_seconds,
        error_message=lesson.error_message,
        created_at=lesson.created_at.isoformat(),
        updated_at=lesson.updated_at.isoformat(),
    )
