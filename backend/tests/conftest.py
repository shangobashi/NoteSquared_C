"""Test configuration and fixtures."""

import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.main import app
from app.database import Base, get_db
from app.auth import get_password_hash, create_access_token
from app.models.user import User


# Create test engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db():
    """Override database dependency for tests."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create database tables and provide session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    # Clean up tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Get authorization headers for test user."""
    token = create_access_token(
        data={"sub": test_user.id, "email": test_user.email}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_student(db_session, test_user):
    """Create a test student."""
    from app.models.student import Student

    student = Student(
        full_name="Test Student",
        instrument="Piano",
        level="BEGINNER",
        parent_email="parent@example.com",
        notes="Test notes",
        owner_id=test_user.id,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student


@pytest_asyncio.fixture
async def test_lesson(db_session, test_student, test_user):
    """Create a test lesson."""
    from app.models.lesson import Lesson, LessonStatus
    from datetime import date

    lesson = Lesson(
        lesson_date=date.today(),
        audio_url="/uploads/test_audio.m4a",
        student_id=test_student.id,
        owner_id=test_user.id,
        status=LessonStatus.UPLOADED,
    )
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)
    return lesson


@pytest_asyncio.fixture
async def completed_lesson(db_session, test_student, test_user):
    """Create a completed lesson with transcript."""
    from app.models.lesson import Lesson, LessonStatus
    from datetime import date

    lesson = Lesson(
        lesson_date=date.today(),
        audio_url="/uploads/test_audio.m4a",
        student_id=test_student.id,
        owner_id=test_user.id,
        status=LessonStatus.COMPLETED,
        transcript="This is a test transcript of the lesson.",
    )
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)
    return lesson


@pytest_asyncio.fixture
async def test_output(db_session, completed_lesson):
    """Create a test output."""
    from app.models.output import Output, OutputType

    output = Output(
        output_type=OutputType.STUDENT_RECAP,
        content="This is a test student recap content.",
        lesson_id=completed_lesson.id,
    )
    db_session.add(output)
    await db_session.commit()
    await db_session.refresh(output)
    return output


@pytest_asyncio.fixture
async def edited_output(db_session, completed_lesson):
    """Create an edited output with original content."""
    from app.models.output import Output, OutputType

    output = Output(
        output_type=OutputType.PRACTICE_PLAN,
        content="Edited practice plan content.",
        original_content="Original practice plan content.",
        is_edited=True,
        lesson_id=completed_lesson.id,
    )
    db_session.add(output)
    await db_session.commit()
    await db_session.refresh(output)
    return output
