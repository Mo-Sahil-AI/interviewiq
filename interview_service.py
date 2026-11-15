import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import InterviewSession, InterviewTurn, Question
from services import get_latest_jd, get_latest_resume

MIN_DURATION_SECONDS = 60
MAX_DURATION_SECONDS = 3600
INTERVIEW_TYPES = {"technical", "behavioral", "mixed", "resume_based"}
ACTIVE_STATUSES = {"preparing", "active"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _lock_key(user_id: uuid.UUID) -> int:
    digest = hashlib.sha256(f"interview:{user_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=True)


def lock_user_interviews(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        text("SELECT pg_advisory_xact_lock(CAST(:lock_key AS bigint))"),
        {"lock_key": _lock_key(user_id)},
    )


def get_owned_session(
    db: Session, user_id: uuid.UUID, session_id: uuid.UUID
) -> InterviewSession | None:
    return db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user_id,
    ).first()


def create_session(
    db: Session,
    user_id: uuid.UUID,
    duration_seconds: int,
    interview_type: str,
) -> InterviewSession:
    if not MIN_DURATION_SECONDS <= duration_seconds <= MAX_DURATION_SECONDS:
        raise ValueError(
            f"duration_seconds must be between {MIN_DURATION_SECONDS} "
            f"and {MAX_DURATION_SECONDS}"
        )
    if interview_type not in INTERVIEW_TYPES:
        raise ValueError("Unsupported interview type")

    lock_user_interviews(db, user_id)
    active = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status.in_(ACTIVE_STATUSES),
    ).first()
    if active is not None:
        raise RuntimeError("An interview is already active")

    resume = get_latest_resume(db, user_id)
    jd = get_latest_jd(db, user_id)
    if resume is None or jd is None:
        raise LookupError("A saved resume and job description are required")

    session = InterviewSession(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume.id,
        resume_version=resume.version_no,
        jd_id=jd.id,
        jd_version=jd.version_no,
        interview_type=interview_type,
        duration_seconds=duration_seconds,
        status="preparing",
    )
    db.add(session)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise RuntimeError("An interview is already active") from None
    db.refresh(session)
    return session


def start_session(db: Session, session: InterviewSession) -> InterviewSession:
    if session.status != "preparing":
        raise ValueError("Only a preparing interview can be started")
    session.status = "active"
    session.started_at = utc_now()
    db.commit()
    db.refresh(session)
    return session


def finish_session(
    db: Session, session: InterviewSession, status: str
) -> InterviewSession:
    if session.status not in ACTIVE_STATUSES:
        raise ValueError("Only an active interview can be finished")
    if status not in {"completed", "interrupted", "failed"}:
        raise ValueError("Unsupported finish status")
    session.status = status
    session.ended_at = utc_now()
    db.commit()
    db.refresh(session)
    return session


def next_question(
    db: Session,
    session: InterviewSession,
) -> tuple[str, str, str]:
    """Return the next saved question for this interview snapshot."""
    answered_question_ids = {
        row[0]
        for row in db.query(InterviewTurn.question_text).filter(
            InterviewTurn.session_id == session.id
        ).all()
    }
    question = db.query(Question).filter(
        Question.user_id == session.user_id,
        Question.resume_id == session.resume_id,
        Question.jd_id == session.jd_id,
        Question.resume_version == session.resume_version,
        Question.jd_version == session.jd_version,
    ).order_by(Question.created_at, Question.item_no).all()
    for candidate in question:
        if candidate.question_text not in answered_question_ids:
            return candidate.question_text, candidate.category, candidate.difficulty

    return (
        "Tell me about the experience most relevant to this role.",
        "resume_based",
        "medium",
    )


def save_answer(
    db: Session,
    session: InterviewSession,
    question_text: str,
    question_category: str,
    difficulty: str,
    transcript: str,
    answer_duration_ms: int,
) -> InterviewTurn:
    turn = InterviewTurn(
        session_id=session.id,
        turn_no=session.current_turn_no + 1,
        question_text=question_text,
        question_category=question_category,
        difficulty=difficulty,
        user_transcript=transcript,
        answer_started_at=utc_now(),
        answer_ended_at=utc_now(),
        answer_duration_ms=answer_duration_ms,
        is_completed=True,
    )
    session.current_turn_no = turn.turn_no
    session.questions_asked += 1
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn
