"""Whisper transcription worker for Render."""

import os
import shutil
import tarfile
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


MODEL_SIZE = os.getenv("MODEL_SIZE", "tiny")
WORKER_AUTH_TOKEN = os.getenv("WORKER_AUTH_TOKEN", "")
FFMPEG_URL = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

app = FastAPI()
_model = None


def _ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return
    tmp_dir = Path("/tmp/ffmpeg")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    archive_path = tmp_dir / "ffmpeg.tar.xz"
    if not archive_path.exists():
        with httpx.stream("GET", FFMPEG_URL, timeout=60) as resp:
            resp.raise_for_status()
            with open(archive_path, "wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
    with tarfile.open(archive_path, "r:xz") as tar:
        tar.extractall(tmp_dir)
    # Find ffmpeg binary
    for path in tmp_dir.rglob("ffmpeg"):
        if path.is_file():
            os.environ["PATH"] = f"{path.parent}:{os.environ.get('PATH','')}"
            return


def _get_model():
    global _model
    if _model is None:
        _ensure_ffmpeg()
        from faster_whisper import WhisperModel

        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


class TranscribeRequest(BaseModel):
    audio_url: str


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_SIZE}


@app.post("/transcribe")
async def transcribe(
    payload: TranscribeRequest,
    x_worker_token: str | None = Header(default=None),
):
    if WORKER_AUTH_TOKEN and x_worker_token != WORKER_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    tmp_dir = Path("/tmp/whisper")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    local_path = tmp_dir / f"audio_{uuid.uuid4()}.bin"

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(payload.audio_url)
        resp.raise_for_status()
        local_path.write_bytes(resp.content)

    model = _get_model()
    segments, _info = model.transcribe(str(local_path))
    text = "".join(segment.text for segment in segments).strip()

    try:
        local_path.unlink(missing_ok=True)
    except Exception:
        pass

    return {"text": text}
