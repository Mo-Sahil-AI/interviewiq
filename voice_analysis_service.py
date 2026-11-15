import re
import uuid
from collections import Counter

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from models import InterviewSession, InterviewTurn, VoiceAnalysis

_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_FILLERS = {
    "um", "uh", "erm", "hmm", "like", "basically", "actually",
    "literally", "you know", "sort of", "kind of",
}


class VoiceMetricsInput(BaseModel):
    duration_ms: int = Field(default=0, ge=0, le=3_600_000)
    pause_count: int = Field(default=0, ge=0, le=1_000)
    long_pause_count: int = Field(default=0, ge=0, le=500)
    recognition_confidence: float | None = Field(default=None, ge=0, le=1)
    language: str = Field(default="en-US", min_length=2, max_length=16)

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.strip() or "en-US"


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _words(transcript: str) -> list[str]:
    return [word.lower() for word in _WORD_RE.findall(transcript)]


def _filler_words(words: list[str]) -> list[str]:
    found = []
    index = 0
    while index < len(words):
        pair = " ".join(words[index:index + 2])
        if pair in _FILLERS:
            found.append(pair)
            index += 2
            continue
        if words[index] in _FILLERS:
            found.append(words[index])
        index += 1
    return found


def _repeated_words(words: list[str]) -> list[str]:
    return [
        word for word, count in Counter(words).items()
        if count > 1 and len(word) > 2
    ]


def analyze_transcript(
    transcript: str,
    metrics: VoiceMetricsInput,
) -> dict:
    words = _words(transcript)
    fillers = _filler_words(words)
    repeated = _repeated_words(words)
    minutes = metrics.duration_ms / 60_000
    wpm = round(len(words) / minutes) if minutes > 0 and words else None

    fluency = _clamp(
        100
        - len(fillers) * 5
        - metrics.long_pause_count * 6
        - metrics.pause_count * 2
    )
    clarity = _clamp(100 - len(repeated) * 3 - len(fillers) * 2)
    grammar = 85 if len(words) >= 12 else 70 if len(words) >= 6 else 55
    if transcript and transcript[-1] in ".!?":
        grammar = min(100, grammar + 5)

    if wpm is None:
        pace = None
    elif 120 <= wpm <= 180:
        pace = 95
    elif 100 <= wpm <= 210:
        pace = 80
    else:
        pace = 60

    feedback = []
    if fillers:
        feedback.append(f"Reduce filler words such as {', '.join(sorted(set(fillers)))}.")
    if metrics.long_pause_count:
        feedback.append("Practice smoother transitions to reduce long pauses.")
    if wpm is not None and pace < 80:
        feedback.append("Aim for a steadier speaking pace around 120-180 words per minute.")
    if len(repeated):
        feedback.append("Avoid repeating the same words while organizing your answer.")
    if not feedback:
        feedback.append("Your transcript shows a clear and reasonably fluent response.")

    return {
        "transcript": transcript,
        "language": metrics.language,
        "speaking_rate_wpm": wpm,
        "pause_count": metrics.pause_count,
        "long_pause_count": metrics.long_pause_count,
        "filler_word_count": len(fillers),
        "repeated_word_count": len(repeated),
        "grammar_score": grammar,
        "fluency_score": fluency,
        "clarity_score": clarity,
        "pronunciation_score": None,
        "confidence_score": (
            round(metrics.recognition_confidence * 100)
            if metrics.recognition_confidence is not None
            else None
        ),
        "pace_score": pace,
        "grammar_issues": [],
        "filler_words": sorted(set(fillers)),
        "pronunciation_notes": [
            "Pronunciation scoring is unavailable in browser speech mode."
        ],
        "voice_feedback": " ".join(feedback),
    }


def save_voice_analysis(
    db: Session,
    session: InterviewSession,
    turn: InterviewTurn,
    metrics: VoiceMetricsInput | None = None,
) -> VoiceAnalysis:
    metrics = metrics or VoiceMetricsInput()
    values = analyze_transcript(turn.user_transcript or "", metrics)
    analysis = db.query(VoiceAnalysis).filter(
        VoiceAnalysis.turn_id == turn.id
    ).first()
    if analysis is None:
        analysis = VoiceAnalysis(
            id=uuid.uuid4(),
            session_id=session.id,
            turn_id=turn.id,
            analysis_status="completed",
            analysis_provider="browser_metrics",
        )
        db.add(analysis)
    for field, value in values.items():
        setattr(analysis, field, value)
    db.commit()
    db.refresh(analysis)
    return analysis
