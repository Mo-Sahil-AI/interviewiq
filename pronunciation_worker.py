import json
import logging
import os
import re
import subprocess
import tempfile
import time
import wave
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from config import (
    LOCAL_PRONUNCIATION_MODEL,
    PRONUNCIATION_PROVIDER,
    PRONUNCIATION_QUEUE_NAME,
    REDIS_URL,
)
from database import SessionLocal
from models import VoiceAnalysis
import redis

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_processor = None
_model = None


def _phoneme_tokens(value: str) -> list[str]:
    return re.findall(r"[^\s|]+", value.lower().strip())


def _load_phoneme_model():
    global _processor, _model
    if _processor is None or _model is None:
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

        logger.info("Loading local pronunciation model %s", LOCAL_PRONUNCIATION_MODEL)
        _processor = Wav2Vec2Processor.from_pretrained(LOCAL_PRONUNCIATION_MODEL)
        _model = Wav2Vec2ForCTC.from_pretrained(LOCAL_PRONUNCIATION_MODEL)
        _model.eval()
    return _processor, _model


def _read_audio(audio_path: str):
    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as converted:
        wav_path = converted.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "16000",
                "-f", "wav", wav_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        with wave.open(wav_path, "rb") as wav_file:
            samples = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)
        return samples.astype(np.float32) / 32768.0
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


def _local_wav2vec2_analysis(audio_path: str, transcript: str) -> dict:
    if not transcript.strip():
        raise ValueError("Transcript is required for pronunciation alignment")
    from phonemizer import phonemize
    import torch

    processor, model = _load_phoneme_model()
    expected = phonemize(
        transcript,
        language="en-us",
        backend="espeak",
        strip=True,
        preserve_punctuation=False,
        with_stress=False,
    )
    expected_tokens = _phoneme_tokens(expected)
    if not expected_tokens:
        raise ValueError("Could not derive phonemes from the transcript")

    audio = _read_audio(audio_path)
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    with torch.inference_mode():
        logits = model(**inputs).logits
    observed = processor.batch_decode(logits.argmax(dim=-1))[0]
    observed_tokens = _phoneme_tokens(observed)
    if not observed_tokens:
        raise ValueError("The local model did not detect phonemes")

    ratio = SequenceMatcher(None, expected_tokens, observed_tokens).ratio()
    score = max(0, min(100, round(ratio * 100)))
    return {
        "pronunciation_score": score,
        "pronunciation_notes": [
            "Approximate local phoneme alignment score.",
            f"Expected {len(expected_tokens)} phonemes; detected {len(observed_tokens)}.",
        ],
    }


def analyze_audio(audio_path: str, transcript: str) -> dict:
    if PRONUNCIATION_PROVIDER == "local_wav2vec2":
        return _local_wav2vec2_analysis(audio_path, transcript)
    raise RuntimeError(
        f"Unsupported pronunciation provider: {PRONUNCIATION_PROVIDER}"
    )


def process_job(payload: dict) -> None:
    db: Session = SessionLocal()
    audio_path = payload["audio_path"]
    try:
        analysis = db.query(VoiceAnalysis).filter(
            VoiceAnalysis.id == payload["analysis_id"]
        ).first()
        if analysis is None:
            return
        analysis.analysis_status = "processing"
        db.commit()
        try:
            result = analyze_audio(audio_path, analysis.transcript or "")
        except Exception as exc:
            analysis.analysis_status = "failed"
            analysis.analysis_provider = "local"
            analysis.analysis_error = str(exc)[:500]
            db.commit()
            logger.warning("Pronunciation analysis failed: %s", exc)
            return
        for field, value in result.items():
            setattr(analysis, field, value)
        analysis.analysis_status = "completed"
        analysis.analysis_provider = "local"
        analysis.analysis_error = None
        db.commit()
    finally:
        db.close()
        if os.path.exists(audio_path):
            os.remove(audio_path)


def run() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Listening on Redis queue %s", PRONUNCIATION_QUEUE_NAME)
    while True:
        item = client.blpop(PRONUNCIATION_QUEUE_NAME, timeout=5)
        if item is None:
            continue
        try:
            process_job(json.loads(item[1]))
        except Exception:
            logger.exception("Unexpected pronunciation job failure")
            time.sleep(1)


if __name__ == "__main__":
    run()
