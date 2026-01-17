"""Note² (Note Squared) - AI Practice Plan Generator for Music Teachers.

Main application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import get_settings
from .database import init_db
from .routes import auth_router, students_router, lessons_router, outputs_router, health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield
    # Shutdown


app = FastAPI(
    title="Note² API",
    description="AI Practice Plan Generator for Music Teachers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Include routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/v1")
app.include_router(students_router, prefix="/v1")
app.include_router(lessons_router, prefix="/v1")
app.include_router(outputs_router, prefix="/v1")


@app.get("/")
async def root():
    """Root endpoint with app info."""
    return {
        "name": "Note² API",
        "version": "1.0.0",
        "description": "AI Practice Plan Generator for Music Teachers",
        "docs": "/docs",
    }
