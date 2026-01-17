"""AI Pipeline for processing lessons.

This module handles:
1. Transcription (via OpenAI Whisper or simulated)
2. Extraction of musical instruction
3. Generation of outputs (Student Recap, Practice Plan, Parent Email)
"""

import asyncio
import os
import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from ..database import async_session_maker
from ..models.lesson import Lesson, LessonStatus
from ..models.output import Output, OutputType
from ..config import get_settings

settings = get_settings()


def _parse_supabase_path(value: str) -> tuple[str, str] | None:
    if not value.startswith("supabase://"):
        return None
    path = value.replace("supabase://", "", 1)
    if "/" not in path:
        return None
    bucket, object_path = path.split("/", 1)
    return bucket, object_path


async def _signed_supabase_url(bucket: str, object_path: str, expires_in: int = 3600) -> str | None:
    if not (settings.supabase_url and settings.supabase_service_role_key):
        return None
    url = f"{settings.supabase_url}/storage/v1/object/sign/{bucket}/{object_path}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json={"expiresIn": expires_in})
        if resp.status_code != 200:
            return None
        data = resp.json()
        signed = data.get("signedURL") or data.get("signedUrl")
        if not signed:
            return None
        return f"{settings.supabase_url}/storage/v1{signed}"


async def _transcribe_via_worker(audio_url: str) -> str | None:
    if not settings.transcription_worker_url:
        return None
    headers = {}
    if settings.transcription_worker_token:
        headers["X-Worker-Token"] = settings.transcription_worker_token
    payload = {"audio_url": audio_url}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.transcription_worker_url.rstrip('/')}/transcribe",
                json=payload,
                headers=headers,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            return data.get("text")
    except Exception:
        return None


async def process_lesson_pipeline(lesson_id: str, student_name: str, instrument: str):
    """Process a lesson through the full AI pipeline."""
    async with async_session_maker() as db:
        try:
            # Get lesson
            result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
            lesson = result.scalar_one_or_none()

            if not lesson:
                return

            # Step 1: Transcription
            lesson.status = LessonStatus.TRANSCRIBING.value
            await db.commit()

            transcript = await transcribe_audio(lesson.audio_url)
            lesson.transcript = transcript

            # Step 2: Extraction
            lesson.status = LessonStatus.EXTRACTING.value
            await db.commit()

            extraction = await extract_musical_instruction(transcript, student_name, instrument)
            lesson.extraction = extraction

            # Step 3: Generation
            lesson.status = LessonStatus.GENERATING.value
            await db.commit()

            outputs = await generate_outputs(extraction, student_name, instrument)

            # Save outputs
            for output_type, content in outputs.items():
                output = Output(
                    lesson_id=lesson.id,
                    output_type=output_type,
                    content=content,
                )
                db.add(output)

            # Mark complete
            lesson.status = LessonStatus.COMPLETED.value
            await db.commit()

        except Exception as e:
            # Mark as failed
            lesson.status = LessonStatus.FAILED.value
            lesson.error_message = str(e)
            await db.commit()
            raise


async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using OpenAI Whisper or simulate."""
    # For demo purposes, simulate transcription
    # In production, this would use OpenAI Whisper API
    await asyncio.sleep(2)  # Simulate processing time

    supabase_parts = _parse_supabase_path(audio_path)
    if supabase_parts:
        signed = await _signed_supabase_url(*supabase_parts)
        if signed and settings.transcription_worker_url:
            worker_text = await _transcribe_via_worker(signed)
            if worker_text:
                return worker_text
        if signed:
            audio_path = signed

    local_path = audio_path
    if audio_path.startswith("http://") or audio_path.startswith("https://"):
        os.makedirs(settings.upload_dir, exist_ok=True)
        tmp_name = f"audio_{uuid.uuid4()}.bin"
        local_path = os.path.join(settings.upload_dir, tmp_name)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(audio_path)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(resp.content)

    # Check if we have an actual OpenAI key
    if settings.openai_api_key and settings.openai_api_key.startswith("sk-"):
        try:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)
            with open(local_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )
                return response.text
        except Exception:
            pass
        finally:
            if local_path != audio_path:
                try:
                    os.remove(local_path)
                except OSError:
                    pass

    if local_path != audio_path:
        try:
            os.remove(local_path)
        except OSError:
            pass

    # Simulated transcript for demo
    return """
Let's start with the C major scale today. Remember to keep your wrists relaxed and your fingers curved.
Good! Try to make each note even. The third finger is a little weak, so really press down with it.

Now let's work on the Bach Minuet. Start from measure 12. The left hand is rushing here -
count "1 and 2 and 3 and" while you play. Good, that's better!

For the Sonatina, I want you to focus on the dynamics. There's a crescendo starting in measure 8
leading up to the forte in measure 12. Make sure you really bring out that contrast.

Your C major scale has improved a lot! The evenness is much better than last week.
Keep practicing with the metronome at 60 BPM this week, then we can speed it up.

For homework this week:
- Practice C major scale hands separate, then hands together, at 60 BPM
- Bach Minuet measures 12-16, left hand only first, then hands together slowly
- Sonatina - work on the crescendo in measures 8-12, really exaggerate the dynamic change
- Try to memorize the first line of the Bach by next week

Great lesson today! You're making excellent progress.
"""


async def extract_musical_instruction(transcript: str, student_name: str, instrument: str) -> dict:
    """Extract structured musical instruction from transcript."""
    await asyncio.sleep(1)  # Simulate processing time

    # For demo, return simulated extraction
    # In production, this would use GPT-4 with JSON mode
    return {
        "student_name": student_name,
        "instrument": instrument,
        "lesson_date": date.today().isoformat(),
        "skills_practiced": [
            {"name": "C Major Scale", "status": "improving", "notes": "Evenness much better"},
            {"name": "Finger Position", "status": "focus_area", "notes": "Keep wrists relaxed, fingers curved"},
        ],
        "repertoire": [
            {
                "piece": "Bach Minuet",
                "focus_measures": "12-16",
                "issues": ["Left hand rushing"],
                "solutions": ["Count 1-and-2-and while playing"],
            },
            {
                "piece": "Sonatina",
                "focus_measures": "8-12",
                "issues": ["Dynamics need work"],
                "solutions": ["Focus on crescendo, exaggerate dynamic change"],
            },
        ],
        "assignments": [
            {"task": "C Major Scale", "details": "Hands separate then together at 60 BPM", "duration_minutes": 5},
            {"task": "Bach Minuet mm. 12-16", "details": "Left hand only, then hands together slowly", "duration_minutes": 10},
            {"task": "Sonatina mm. 8-12", "details": "Work on crescendo, exaggerate dynamics", "duration_minutes": 5},
            {"task": "Bach memorization", "details": "Memorize first line", "duration_minutes": 5},
        ],
        "positive_feedback": [
            "C major scale evenness improved significantly",
            "Good progress on finger technique",
        ],
        "areas_for_improvement": [
            "Left hand coordination in Bach",
            "Dynamic expression in Sonatina",
        ],
    }


async def generate_outputs(extraction: dict, student_name: str, instrument: str) -> dict[str, str]:
    """Generate all three outputs from extraction."""
    await asyncio.sleep(1)  # Simulate processing time

    today = date.today()
    today_str = today.strftime("%B %d")

    # Generate Student Recap
    student_recap = f"""# Lesson Recap - {today_str}

## What Went Well

- Your C major scale had excellent evenness today - much improved from last week!
- Great job maintaining relaxed wrists and curved fingers
- The Bach Minuet is coming along nicely

## Areas to Focus On

- Left hand is rushing in measures 12-16 of the Bach - remember to count "1-and-2-and"
- Work on the dynamics in the Sonatina, especially the crescendo in measures 8-12

## Teacher's Note

Really proud of your progress this week! The scale work is paying off. Keep up the great practice habits and you'll be ready to increase the tempo soon.
"""

    # Generate Practice Plan
    assignments = extraction.get("assignments", [])
    practice_plan = f"""# Practice Plan - {today_str} to {(today.replace(day=today.day + 6)).strftime("%B %d")}

## Day 1
- [ ] C Major Scale: hands separate, then together at 60 BPM (5 min)
- [ ] Bach Minuet: measures 12-16, left hand only (10 min)
- [ ] Sonatina: play through measures 8-12 focusing on dynamics (5 min)

## Day 2
- [ ] C Major Scale: hands together at 60 BPM (5 min)
- [ ] Bach Minuet: measures 12-16, hands together slowly (10 min)
- [ ] Sonatina: exaggerate the crescendo in measures 8-12 (5 min)

## Day 3
- [ ] C Major Scale: hands together, focus on weak third finger (5 min)
- [ ] Bach Minuet: full piece, slow tempo (10 min)
- [ ] Sonatina: work on dynamic contrast (5 min)

## Day 4
- [ ] C Major Scale: increase tempo if comfortable (5 min)
- [ ] Bach Minuet: memorize first line (10 min)
- [ ] Sonatina: play through with all dynamics (5 min)

## Day 5
- [ ] C Major Scale: hands together at comfortable tempo (5 min)
- [ ] Bach Minuet: review memorized section (10 min)
- [ ] Sonatina: record yourself and listen back (5 min)

## Day 6
- [ ] C Major Scale: hands together, smooth and even (5 min)
- [ ] Bach Minuet: practice hands together at performance tempo (10 min)
- [ ] Sonatina: full run-through with dynamics (5 min)

## Day 7 (Light Review)
- [ ] Play through all pieces once, noting any trouble spots
- [ ] Review memorized Bach section

**Weekly Goal**: Memorize the first line of the Bach Minuet and maintain even tempo in measures 12-16.
"""

    # Generate Parent Email
    parent_email = f"""**Subject**: {student_name}'s {instrument} Lesson - {today_str}

Dear Parent,

{student_name} had a wonderful lesson today! Here are the highlights:

**Progress This Week:**
- The C major scale has improved significantly - the evenness and finger technique are much better
- Good work on maintaining proper hand position with relaxed wrists

**Focus Areas:**
This week, we're concentrating on:
- Bach Minuet measures 12-16 (left hand coordination)
- Sonatina dynamics, especially the crescendo in measures 8-12

**Practice Reminders:**
- C Major Scale at 60 BPM daily (5 minutes)
- Bach Minuet measures 12-16, left hand first, then hands together (10 minutes)
- Sonatina measures 8-12, focusing on dynamic changes (5 minutes)

Please encourage {student_name} to use the metronome during scale practice - it really helps with evenness!

I've attached a detailed practice plan for the week. Let me know if you have any questions.

Best regards,
[Teacher Name]
"""

    return {
        OutputType.STUDENT_RECAP.value: student_recap,
        OutputType.PRACTICE_PLAN.value: practice_plan,
        OutputType.PARENT_EMAIL.value: parent_email,
    }
