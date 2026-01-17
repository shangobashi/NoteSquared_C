"""Health check endpoint."""

import httpx
from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": "NoteÂ² API"}


@router.get("/cron/ping-worker")
async def ping_worker():
    """Keep the transcription worker warm."""
    if not settings.transcription_worker_url:
        return {"status": "skipped", "reason": "no worker url configured"}
    url = f"{settings.transcription_worker_url.rstrip('/')}/health"
    headers = {}
    if settings.transcription_worker_token:
        headers["X-Worker-Token"] = settings.transcription_worker_token
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            return {"status": "ok", "code": resp.status_code}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
