"""Student management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.user import User
from ..models.student import Student, StudentLevel
from ..auth import get_current_user

router = APIRouter(prefix="/students", tags=["students"])


# Available instruments
INSTRUMENTS = [
    "Piano", "Violin", "Viola", "Cello", "Guitar", "Voice",
    "Flute", "Clarinet", "Saxophone", "Trumpet", "Drums", "Other"
]


class StudentCreate(BaseModel):
    """Create student request."""
    full_name: str
    instrument: str
    level: str = StudentLevel.BEGINNER.value
    parent_email: EmailStr | None = None
    parent_name: str | None = None
    notes: str | None = None


class StudentUpdate(BaseModel):
    """Update student request."""
    full_name: str | None = None
    instrument: str | None = None
    level: str | None = None
    parent_email: EmailStr | None = None
    parent_name: str | None = None
    notes: str | None = None


class StudentResponse(BaseModel):
    """Student response."""
    id: str
    full_name: str
    instrument: str
    level: str
    parent_email: str | None
    parent_name: str | None
    notes: str | None
    is_archived: bool
    created_at: str
    updated_at: str
    lesson_count: int = 0

    class Config:
        from_attributes = True


@router.get("/instruments")
async def get_instruments():
    """Get list of available instruments."""
    return {"instruments": INSTRUMENTS}


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    request: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new student."""
    student = Student(
        owner_id=current_user.id,
        full_name=request.full_name,
        instrument=request.instrument,
        level=request.level,
        parent_email=request.parent_email,
        parent_name=request.parent_name,
        notes=request.notes,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)

    return StudentResponse(
        id=student.id,
        full_name=student.full_name,
        instrument=student.instrument,
        level=student.level,
        parent_email=student.parent_email,
        parent_name=student.parent_name,
        notes=student.notes,
        is_archived=student.is_archived,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat(),
        lesson_count=0,
    )


@router.get("", response_model=list[StudentResponse])
async def list_students(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all students."""
    query = select(Student).options(selectinload(Student.lessons)).where(Student.owner_id == current_user.id)
    if not include_archived:
        query = query.where(Student.is_archived == False)
    query = query.order_by(Student.full_name)

    result = await db.execute(query)
    students = result.scalars().all()

    return [
        StudentResponse(
            id=s.id,
            full_name=s.full_name,
            instrument=s.instrument,
            level=s.level,
            parent_email=s.parent_email,
            parent_name=s.parent_name,
            notes=s.notes,
            is_archived=s.is_archived,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            lesson_count=len(s.lessons) if s.lessons else 0,
        )
        for s in students
    ]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a student by ID."""
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.lessons))
        .where(
            Student.id == student_id,
            Student.owner_id == current_user.id,
        )
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return StudentResponse(
        id=student.id,
        full_name=student.full_name,
        instrument=student.instrument,
        level=student.level,
        parent_email=student.parent_email,
        parent_name=student.parent_name,
        notes=student.notes,
        is_archived=student.is_archived,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat(),
        lesson_count=len(student.lessons) if student.lessons else 0,
    )


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    request: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a student."""
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.lessons))
        .where(
            Student.id == student_id,
            Student.owner_id == current_user.id,
        )
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    await db.flush()
    await db.refresh(student)

    return StudentResponse(
        id=student.id,
        full_name=student.full_name,
        instrument=student.instrument,
        level=student.level,
        parent_email=student.parent_email,
        parent_name=student.parent_name,
        notes=student.notes,
        is_archived=student.is_archived,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat(),
        lesson_count=len(student.lessons) if student.lessons else 0,
    )


@router.post("/{student_id}/archive", response_model=StudentResponse)
async def archive_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive a student."""
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.lessons))
        .where(
            Student.id == student_id,
            Student.owner_id == current_user.id,
        )
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    student.is_archived = True
    await db.flush()
    await db.refresh(student)

    return StudentResponse(
        id=student.id,
        full_name=student.full_name,
        instrument=student.instrument,
        level=student.level,
        parent_email=student.parent_email,
        parent_name=student.parent_name,
        notes=student.notes,
        is_archived=student.is_archived,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat(),
        lesson_count=len(student.lessons) if student.lessons else 0,
    )
