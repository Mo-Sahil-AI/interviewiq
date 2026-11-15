import json
import os
import tempfile
import time
import uuid

import redis
from sqlalchemy.orm import Session

from config import AUDIO_RETENTION_SECONDS, PRONUNCIATION_QUEUE_NAME, REDIS_URL
from models import InterviewSession, InterviewTurn, VoiceAnalysis

_AUDIO_DIR = os.path.join(tempfile.gettempdir(), "interviewiq-audio")
os.makedirs(_AUDIO_DIR, exist_ok=True)


def _client() -> redis.Redis:
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


def _remove_stale_audio() -> None:
    cutoff = time.time()
    for name in os.listdir(_AUDIO_DIR):
        path = os.path.join(_AUDIO_DIR, name)
        try:
            if (
                os.path.isfile(path)
                and cutoff - os.path.getmtime(path) > AUDIO_RETENTION_SECONDS
            ):
                os.remove(path)
        except OSError:
            continue


def enqueue(
    db: Session,
    session: InterviewSession,
    turn: InterviewTurn,
    analysis: VoiceAnalysis,
    audio_bytes: bytes,
    content_type: str = "audio/webm",
) -> bool:
    if not audio_bytes:
        return False
    _remove_stale_audio()
    suffix = ".webm" if "webm" in content_type else ".audio"
    path = os.path.join(_AUDIO_DIR, f"{uuid.uuid4().hex}{suffix}")
    with open(path, "wb") as audio_file:
        audio_file.write(audio_bytes)

    payload = {
        "session_id": str(session.id),
        "turn_id": str(turn.id),
        "analysis_id": str(analysis.id),
        "audio_path": path,
        "content_type": content_type,
    }
    client = _client()
    try:
        client.rpush(PRONUNCIATION_QUEUE_NAME, json.dumps(payload))
    except redis.RedisError:
        os.remove(path)
        analysis.analysis_status = "failed"
        analysis.analysis_error = "Pronunciation queue is unavailable"
        db.commit()
        return False

    analysis.analysis_status = "queued"
    analysis.analysis_provider = "background"
    analysis.analysis_error = None
    db.commit()
    return True
