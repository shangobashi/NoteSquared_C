"""API Routes."""

from .auth import router as auth_router
from .students import router as students_router
from .lessons import router as lessons_router
from .outputs import router as outputs_router
from .health import router as health_router

__all__ = ["auth_router", "students_router", "lessons_router", "outputs_router", "health_router"]
