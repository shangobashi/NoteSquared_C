"""Output management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.user import User
from ..models.lesson import Lesson
from ..models.output import Output
from ..auth import get_current_user

router = APIRouter(prefix="/outputs", tags=["outputs"])


class OutputUpdateRequest(BaseModel):
    """Update output request."""
    content: str


class OutputResponse(BaseModel):
    """Output response."""
    id: str
    lesson_id: str
    output_type: str
    content: str
    original_content: str | None
    is_edited: bool
    is_shared: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/{output_id}", response_model=OutputResponse)
async def get_output(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an output by ID."""
    result = await db.execute(
        select(Output)
        .options(selectinload(Output.lesson))
        .where(Output.id == output_id)
    )
    output = result.scalar_one_or_none()

    if not output or output.lesson.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    return OutputResponse(
        id=output.id,
        lesson_id=output.lesson_id,
        output_type=output.output_type,
        content=output.content,
        original_content=output.original_content,
        is_edited=output.is_edited,
        is_shared=output.is_shared,
        created_at=output.created_at.isoformat(),
        updated_at=output.updated_at.isoformat(),
    )


@router.patch("/{output_id}", response_model=OutputResponse)
async def update_output(
    output_id: str,
    request: OutputUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an output's content."""
    result = await db.execute(
        select(Output)
        .options(selectinload(Output.lesson))
        .where(Output.id == output_id)
    )
    output = result.scalar_one_or_none()

    if not output or output.lesson.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Save original if not already edited
    if not output.is_edited:
        output.original_content = output.content

    output.content = request.content
    output.is_edited = True

    await db.flush()
    await db.refresh(output)

    return OutputResponse(
        id=output.id,
        lesson_id=output.lesson_id,
        output_type=output.output_type,
        content=output.content,
        original_content=output.original_content,
        is_edited=output.is_edited,
        is_shared=output.is_shared,
        created_at=output.created_at.isoformat(),
        updated_at=output.updated_at.isoformat(),
    )


@router.post("/{output_id}/share", response_model=OutputResponse)
async def mark_shared(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an output as shared (copied)."""
    result = await db.execute(
        select(Output)
        .options(selectinload(Output.lesson))
        .where(Output.id == output_id)
    )
    output = result.scalar_one_or_none()

    if not output or output.lesson.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    output.is_shared = True
    await db.flush()
    await db.refresh(output)

    return OutputResponse(
        id=output.id,
        lesson_id=output.lesson_id,
        output_type=output.output_type,
        content=output.content,
        original_content=output.original_content,
        is_edited=output.is_edited,
        is_shared=output.is_shared,
        created_at=output.created_at.isoformat(),
        updated_at=output.updated_at.isoformat(),
    )


@router.post("/{output_id}/revert", response_model=OutputResponse)
async def revert_output(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revert an output to its original content."""
    result = await db.execute(
        select(Output)
        .options(selectinload(Output.lesson))
        .where(Output.id == output_id)
    )
    output = result.scalar_one_or_none()

    if not output or output.lesson.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    if not output.original_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No original content to revert to",
        )

    output.content = output.original_content
    output.is_edited = False

    await db.flush()
    await db.refresh(output)

    return OutputResponse(
        id=output.id,
        lesson_id=output.lesson_id,
        output_type=output.output_type,
        content=output.content,
        original_content=output.original_content,
        is_edited=output.is_edited,
        is_shared=output.is_shared,
        created_at=output.created_at.isoformat(),
        updated_at=output.updated_at.isoformat(),
    )
