import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnected

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    TokenRevocationUnavailableError,
    check_redis,
    create_access_token,
    get_current_user,
    get_current_websocket_user,
    hash_password,
    revoke_token,
    verify_password,
)
import account_service
import adaptive_interviewer
import assistant_service
import audio_analysis_queue
import email_service
import interview_summary_service
import interview_service
import question_service
import services as ai_services
import services_auth
import speech_service
import voice_analysis_service
from config import (
    AUTO_CREATE_TABLES,
    COOKIE_SECURE,
    GOOGLE_API_KEY,
    SENTRY_DSN,
    SENTRY_ENVIRONMENT,
    SENTRY_TRACES_SAMPLE_RATE,
    SPEECH_PROVIDER,
)
from database import Base, engine, get_db
from models import (
    InterviewSession,
    InterviewSummary,
    InterviewTurn,
    JobDescription,
    Question,
    Resume,
    ResumeAnalysis,
    User,
    UserProfile,
    VoiceAnalysis,
    AssistantMessage,
)
from schemas import (
    DEFAULT_QUESTION_COUNT,
    AnalysisResponse,
    AssistantConversationResponse,
    AssistantMessageOut,
    AssistantMessageRequest,
    CategoryInfo,
    DifficultyInfo,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    LoginRequest,
    QuestionCategory,
    QuestionListResponse,
    QuestionOptionsResponse,
    QuestionOut,
    RegisterRequest,
    RegisterResponse,
    ChangePasswordRequest,
    CreateInterviewRequest,
    InterviewSessionListResponse,
    InterviewSessionOut,
    InterviewReviewResponse,
    InterviewTurnReviewOut,
    InterviewSummaryOut,
    PasswordRequest,
    PasswordResetRequest,
    TokenRequest,
    VoiceAnalysisOut,
)
from services import (
    AnalysisUnavailableError,
    InvalidInputError,
    MissingInputError,
    process_submission,
)
from services_auth import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
REQUEST_COUNT = Counter(
    "interviewiq_http_requests_total",
    "Total HTTP requests",
    ("method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "interviewiq_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "path"),
)

if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
    )

if AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)

app = FastAPI()
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024                 # 5 MB resume
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 256 * 1024  # + job description and form overhead
MAX_INTERVIEW_AUDIO_BYTES = 10 * 1024 * 1024


# ---------------------------------------------------------------------------
# Application and operational endpoints
# ---------------------------------------------------------------------------

@app.get("/health/live", include_in_schema=False)
def health_live():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def app_home():
    return FileResponse(STATIC_DIR / "app.html")


@app.get("/interview", include_in_schema=False)
def interview_page():
    return FileResponse(STATIC_DIR / "interview.html")


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health/ready", include_in_schema=False)
def health_ready(db: Session = Depends(get_db)):
    checks = {
        "database": False,
        "redis": False,
        "ai": bool(GOOGLE_API_KEY and ai_services.client),
    }

    try:
        tables = db.execute(
            text(
                "SELECT to_regclass('public.users') AS users_table, "
                "to_regclass('public.questions') AS questions_table, "
                "to_regclass('public.interview_sessions') AS interview_sessions_table"
            )
        ).one()
        checks["database"] = (
            tables.users_table is not None
            and tables.questions_table is not None
            and tables.interview_sessions_table is not None
        )
    except SQLAlchemyError:
        logging.getLogger(__name__).exception("Readiness database check failed")

    try:
        check_redis()
        checks["redis"] = True
    except TokenRevocationUnavailableError:
        pass

    if not all(checks.values()):
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - started_at
        REQUEST_COUNT.labels(request.method, request.url.path, "500").inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
        logger.exception(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        raise

    duration = time.perf_counter() - started_at
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(self), geolocation=(), payment=()"
    )
    REQUEST_COUNT.labels(
        request.method, request.url.path, str(response.status_code)
    ).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )
    return response


@app.middleware("http")
async def reject_oversized_requests(request: Request, call_next):
    """Turn away obviously huge uploads before the server reads them.
    (Requests without a Content-Length are still limited inside /analyze.)"""
    if request.method == "POST" and request.url.path == "/analyze":
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Upload too large (the resume can be at most 5 MB)."},
            )
    return await call_next(request)


RESET_FIX_JS = """
// endpoints that should clear the /analyze form when you run them
const CLEAR_AFTER = ["/login", "/logout"];

function blockPath(block) {
  const p = block.querySelector(".opblock-summary-path");
  if (!p) return "";
  return p.getAttribute("data-path") || p.textContent.trim();
}

function findBlock(path) {
  return Array.from(document.querySelectorAll(".opblock")).find(function (b) {
    return blockPath(b) === path;
  });
}

function findButton(block, label) {
  return Array.from(block.querySelectorAll("button")).find(function (b) {
    return b.textContent.trim() === label;
  });
}

function wipeFields(block) {
  // wait for Swagger to finish its own reset, then clear everything
  setTimeout(function () {
    block.querySelectorAll('input[type="file"]').forEach(function (inp) {
      inp.value = "";
      inp.dispatchEvent(new Event("change", { bubbles: true }));
    });

    block.querySelectorAll('input[type="text"], textarea').forEach(function (inp) {
      const proto = inp.tagName === "TEXTAREA"
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(proto, "value").set.call(inp, "");
      inp.dispatchEvent(new Event("input", { bubbles: true }));
    });
  }, 150);
}

document.addEventListener("click", function (e) {
  const btn = e.target.closest("button");
  if (!btn) return;

  const block = btn.closest(".opblock");
  if (!block) return;

  const label = btn.textContent.trim();

  // 1) Reset clicked on an endpoint with a file field (only /analyze)
  if (label === "Reset" && block.querySelector('input[type="file"]')) {
    wipeFields(block);
    return;
  }

  // 2) Execute clicked on /login or /logout: press Reset on /analyze
  if (label === "Execute" && CLEAR_AFTER.indexOf(blockPath(block)) !== -1) {
    const analyze = findBlock("/analyze");
    if (!analyze) return;

    const reset = findButton(analyze, "Reset");
    if (reset) reset.click();   // case 1 above then clears the file and text
  }
});
"""

@app.get("/docs", include_in_schema=False)
def custom_docs():
    page = get_swagger_ui_html(openapi_url="/openapi.json", title="API docs")
    html = bytes(page.body).decode("utf-8").replace(
    "</body>", f"<script>{RESET_FIX_JS}</script></body>"
)
    return HTMLResponse(html)


ALLOWED_EXTENSIONS = {".pdf"}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@app.post("/register", response_model=RegisterResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, request.email, request.password)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="Email already registered")

    verification_message = (
        "Account created. Check your email to verify your address."
    )
    try:
        verification_token = account_service.issue_email_verification(db, user)
        email_service.send_email(
            user.email,
            "Verify your InterviewIQ email",
            (
                "Use this verification token with "
                "POST /account/verify-email:\n\n"
                f"{verification_token}"
            ),
        )
    except email_service.EmailConfigurationError:
        logger.warning(
            "Email verification was not sent because SMTP is not configured"
        )
        verification_message = (
            "Account created. Configure email delivery to verify your address."
        )

    return {"message": verification_message, "email": user.email}


@app.post("/login")
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, request.email, request.password)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,    # JavaScript can't read it
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,   # 2 days
    )

    return {"message": "Logged in"}


@app.post("/logout")
def logout(request: Request, response: Response):
    # Deleting the cookie only logs this browser out. Also cancel the token itself,
    # so a copy of it stops working immediately.
    token = request.cookies.get(COOKIE_NAME)
    if token:
        try:
            revoke_token(token)
        except TokenRevocationUnavailableError:
            response.delete_cookie(
                key=COOKIE_NAME,
                httponly=True,
                secure=COOKIE_SECURE,
                samesite="lax",
            )
            response.status_code = 503
            return {"detail": "Session service is temporarily unavailable"}

    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return {"message": "Logged out"}


@app.delete("/account", status_code=204)
def delete_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete the authenticated user and all owned documents."""
    user_id = current_user.id
    try:
        # Clear references from the profile before deleting the records it points to.
        db.query(UserProfile).filter(UserProfile.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(AssistantMessage).filter(
            AssistantMessage.user_id == user_id
        ).delete(synchronize_session=False)
        db.query(Question).filter(Question.user_id == user_id).delete(
            synchronize_session=False
        )
        session_ids = [
            row[0] for row in db.query(InterviewSession.id).filter(
                InterviewSession.user_id == user_id
            ).all()
        ]
        if session_ids:
            db.query(VoiceAnalysis).filter(
                VoiceAnalysis.session_id.in_(session_ids)
            ).delete(synchronize_session=False)
            db.query(InterviewSummary).filter(
                InterviewSummary.session_id.in_(session_ids)
            ).delete(synchronize_session=False)
            db.query(InterviewTurn).filter(
                InterviewTurn.session_id.in_(session_ids)
            ).delete(synchronize_session=False)
            db.query(InterviewSession).filter(
                InterviewSession.id.in_(session_ids)
            ).delete(synchronize_session=False)
        db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(Resume).filter(Resume.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(JobDescription).filter(JobDescription.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.id == user_id).delete(
            synchronize_session=False
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logging.getLogger(__name__).exception(
            "Account deletion failed", extra={"user_id": str(user_id)}
        )
        raise HTTPException(
            status_code=500,
            detail="Account deletion failed",
        )

    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    response.status_code = 204
    return response


# ---------------------------------------------------------------------------
# Account management
# ---------------------------------------------------------------------------

@app.get("/account/overview")
def account_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.version_no.desc()).first()
    job_description = db.query(JobDescription).filter(
        JobDescription.user_id == current_user.id
    ).order_by(JobDescription.version_no.desc()).first()
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.user_id == current_user.id
    ).order_by(ResumeAnalysis.analysis_version.desc()).first()
    return {
        "email": current_user.email,
        "resume": None if resume is None else {
            "id": str(resume.id),
            "version_no": resume.version_no,
            "file_name": resume.file_name,
            "created_at": resume.created_at,
        },
        "job_description": None if job_description is None else {
            "id": str(job_description.id),
            "version_no": job_description.version_no,
            "created_at": job_description.created_at,
        },
        "analysis": None if analysis is None else {
            "id": str(analysis.id),
            "analysis_version": analysis.analysis_version,
            "overview": analysis.overview,
            "match_analysis": analysis.match_analysis,
            "missing_requirements": analysis.missing_requirements,
            "suggestions": analysis.suggestions,
            "others": analysis.others,
        },
        "question_count": db.query(Question).filter(
            Question.user_id == current_user.id
        ).count(),
        "interview_count": db.query(InterviewSession).filter(
            InterviewSession.user_id == current_user.id
        ).count(),
    }


@app.get(
    "/assistant/messages",
    response_model=AssistantConversationResponse,
)
def get_assistant_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.user_id == current_user.id)
        .order_by(AssistantMessage.created_at.desc())
        .limit(assistant_service.MAX_HISTORY_MESSAGES)
        .all()
    )
    return {"messages": list(reversed(messages))}


@app.post(
    "/assistant/messages",
    response_model=AssistantMessageOut,
    status_code=201,
)
def send_assistant_message(
    request: AssistantMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history_rows = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.user_id == current_user.id)
        .order_by(AssistantMessage.created_at.desc())
        .limit(assistant_service.MAX_HISTORY_MESSAGES)
        .all()
    )
    history = [
        {"role": item.role, "content": item.content}
        for item in reversed(history_rows)
    ]
    user_message = AssistantMessage(
        user_id=current_user.id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()
    try:
        context = assistant_service.build_user_context(db, current_user.id)
        reply = assistant_service.generate_reply(request.message, context, history)
    except AnalysisUnavailableError as exc:
        db.delete(user_message)
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        db.delete(user_message)
        db.commit()
        logger.exception("Personal assistant request failed")
        raise HTTPException(
            status_code=500,
            detail="The assistant could not answer right now.",
        ) from exc

    assistant_message = AssistantMessage(
        user_id=current_user.id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message


@app.delete("/assistant/messages", status_code=204)
def clear_assistant_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(AssistantMessage).filter(
        AssistantMessage.user_id == current_user.id
    ).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=204)


@app.get("/account/export")
def export_account_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all user-owned application data without credentials or tokens."""
    user_id = current_user.id
    resumes = db.query(Resume).filter(Resume.user_id == user_id).order_by(
        Resume.version_no
    ).all()
    job_descriptions = db.query(JobDescription).filter(
        JobDescription.user_id == user_id
    ).order_by(JobDescription.version_no).all()
    analyses = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.user_id == user_id
    ).order_by(ResumeAnalysis.analysis_version).all()
    questions = db.query(Question).filter(Question.user_id == user_id).order_by(
        Question.batch_no, Question.item_no
    ).all()
    assistant_messages = db.query(AssistantMessage).filter(
        AssistantMessage.user_id == user_id
    ).order_by(AssistantMessage.created_at).all()

    export = {
        "exported_at": datetime.now(timezone.utc),
        "account": {
            "email": current_user.email,
            "created_at": current_user.created_at,
        },
        "resumes": [
            {
                "id": resume.id,
                "version_no": resume.version_no,
                "file_name": resume.file_name,
                "resume_text": resume.resume_text,
                "resume_hash": resume.resume_hash,
                "created_at": resume.created_at,
            }
            for resume in resumes
        ],
        "job_descriptions": [
            {
                "id": jd.id,
                "version_no": jd.version_no,
                "job_description": jd.job_description,
                "jd_hash": jd.jd_hash,
                "created_at": jd.created_at,
            }
            for jd in job_descriptions
        ],
        "analyses": [
            {
                "id": analysis.id,
                "analysis_version": analysis.analysis_version,
                "resume_id": analysis.resume_id,
                "jd_id": analysis.jd_id,
                "resume_version": analysis.resume_version,
                "jd_version": analysis.jd_version,
                "overview": analysis.overview,
                "match_analysis": analysis.match_analysis,
                "irrelevant_content": analysis.irrelevant_content,
                "missing_requirements": analysis.missing_requirements,
                "suggestions": analysis.suggestions,
                "others": analysis.others,
                "analysis_hash": analysis.analysis_hash,
                "created_at": analysis.created_at,
            }
            for analysis in analyses
        ],
        "questions": [
            {
                "id": question.id,
                "batch_no": question.batch_no,
                "item_no": question.item_no,
                "resume_id": question.resume_id,
                "jd_id": question.jd_id,
                "resume_version": question.resume_version,
                "jd_version": question.jd_version,
                "analysis_id": question.analysis_id,
                "category": question.category,
                "difficulty": question.difficulty,
                "target_skill": question.target_skill,
                "question_text": question.question_text,
                "question_hash": question.question_hash,
                "ideal_answer_points": question.ideal_answer_points,
                "created_at": question.created_at,
            }
            for question in questions
        ],
        "assistant_messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in assistant_messages
        ],
        "interviews": [],
    }

    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id
    ).order_by(InterviewSession.created_at).all()
    for session in sessions:
        turns = db.query(InterviewTurn).filter(
            InterviewTurn.session_id == session.id
        ).order_by(InterviewTurn.turn_no).all()
        voice_analyses = db.query(VoiceAnalysis).filter(
            VoiceAnalysis.session_id == session.id
        ).order_by(VoiceAnalysis.created_at).all()
        summary = db.query(InterviewSummary).filter(
            InterviewSummary.session_id == session.id
        ).first()
        export["interviews"].append({
            "id": session.id,
            "resume_id": session.resume_id,
            "resume_version": session.resume_version,
            "jd_id": session.jd_id,
            "jd_version": session.jd_version,
            "interview_type": session.interview_type,
            "duration_seconds": session.duration_seconds,
            "status": session.status,
            "current_turn_no": session.current_turn_no,
            "questions_asked": session.questions_asked,
            "overall_score": session.overall_score,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "created_at": session.created_at,
            "turns": [
                {
                    "id": turn.id,
                    "turn_no": turn.turn_no,
                    "question_text": turn.question_text,
                    "question_category": turn.question_category,
                    "difficulty": turn.difficulty,
                    "user_transcript": turn.user_transcript,
                    "answer_started_at": turn.answer_started_at,
                    "answer_ended_at": turn.answer_ended_at,
                    "answer_duration_ms": turn.answer_duration_ms,
                    "answer_score": turn.answer_score,
                    "answer_feedback": turn.answer_feedback,
                    "is_completed": turn.is_completed,
                    "created_at": turn.created_at,
                }
                for turn in turns
            ],
            "voice_analyses": [
                {
                    "id": voice.id,
                    "turn_id": voice.turn_id,
                    "transcript": voice.transcript,
                    "language": voice.language,
                    "speaking_rate_wpm": voice.speaking_rate_wpm,
                    "pause_count": voice.pause_count,
                    "long_pause_count": voice.long_pause_count,
                    "filler_word_count": voice.filler_word_count,
                    "repeated_word_count": voice.repeated_word_count,
                    "grammar_score": voice.grammar_score,
                    "fluency_score": voice.fluency_score,
                    "clarity_score": voice.clarity_score,
                    "pronunciation_score": voice.pronunciation_score,
                    "confidence_score": voice.confidence_score,
                    "pace_score": voice.pace_score,
                    "grammar_issues": voice.grammar_issues,
                    "filler_words": voice.filler_words,
                    "pronunciation_notes": voice.pronunciation_notes,
                    "voice_feedback": voice.voice_feedback,
                    "created_at": voice.created_at,
                }
                for voice in voice_analyses
            ],
            "summary": (
                {
                    "id": summary.id,
                    "overall_score": summary.overall_score,
                    "strong_areas": summary.strong_areas,
                    "weak_areas": summary.weak_areas,
                    "skills_to_learn": summary.skills_to_learn,
                    "job_requirements_missing": summary.job_requirements_missing,
                    "technical_feedback": summary.technical_feedback,
                    "behavioral_feedback": summary.behavioral_feedback,
                    "communication_feedback": summary.communication_feedback,
                    "recommendations": summary.recommendations,
                    "summary_text": summary.summary_text,
                    "created_at": summary.created_at,
                }
                if summary is not None
                else None
            ),
        })
    return export


# ---------------------------------------------------------------------------
# Interview lifecycle
# ---------------------------------------------------------------------------

@app.post("/interviews", response_model=InterviewSessionOut, status_code=201)
def create_interview(
    request: CreateInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return interview_service.create_session(
            db,
            current_user.id,
            request.duration_seconds,
            request.interview_type,
        )
    except LookupError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/interviews", response_model=InterviewSessionListResponse)
def list_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.created_at.desc()).all()
    return {"total": len(items), "items": items}


@app.get("/interviews/{session_id}", response_model=InterviewSessionOut)
def get_interview(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = interview_service.get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    return session


@app.get("/interviews/{session_id}/summary", response_model=InterviewSummaryOut)
def get_interview_summary(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = interview_service.get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    summary = db.query(InterviewSummary).filter(
        InterviewSummary.session_id == session.id,
        InterviewSummary.user_id == current_user.id,
    ).first()
    if summary is None:
        raise HTTPException(status_code=404, detail="Interview summary not found")
    return summary


@app.get("/interviews/{session_id}/review", response_model=InterviewReviewResponse)
def get_interview_review(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = interview_service.get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")

    summary = db.query(InterviewSummary).filter(
        InterviewSummary.session_id == session.id,
        InterviewSummary.user_id == current_user.id,
    ).first()
    turns = db.query(InterviewTurn).filter(
        InterviewTurn.session_id == session.id
    ).order_by(InterviewTurn.turn_no).all()
    voice_by_turn = {
        voice.turn_id: voice
        for voice in db.query(VoiceAnalysis).filter(
            VoiceAnalysis.session_id == session.id
        ).all()
    }

    review_turns = []
    for turn in turns:
        review_turns.append(
            InterviewTurnReviewOut.model_validate({
                "id": turn.id,
                "turn_no": turn.turn_no,
                "question_text": turn.question_text,
                "question_category": turn.question_category,
                "difficulty": turn.difficulty,
                "user_transcript": turn.user_transcript,
                "answer_duration_ms": turn.answer_duration_ms,
                "answer_score": turn.answer_score,
                "answer_feedback": turn.answer_feedback,
                "is_completed": turn.is_completed,
                "voice": (
                    VoiceAnalysisOut.model_validate(voice_by_turn[turn.id])
                    if turn.id in voice_by_turn
                    else None
                ),
            })
        )

    return InterviewReviewResponse(
        session=session,
        summary=summary,
        turns=review_turns,
    )


@app.post("/interviews/{session_id}/start", response_model=InterviewSessionOut)
def start_interview(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = interview_service.get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    try:
        return interview_service.start_session(db, session)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/interviews/{session_id}/finish", response_model=InterviewSessionOut)
def finish_interview(
    session_id: uuid.UUID,
    status: str = Query("completed", pattern="^(completed|interrupted|failed)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = interview_service.get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    try:
        finished = interview_service.finish_session(db, session, status)
        if status == "completed":
            interview_summary_service.create_or_update_summary(db, finished)
        return finished
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.delete("/interviews/{session_id}", status_code=204)
def delete_interview(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = interview_service.get_owned_session(db, current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    db.query(VoiceAnalysis).filter(
        VoiceAnalysis.session_id == session.id
    ).delete(synchronize_session=False)
    db.query(InterviewSummary).filter(
        InterviewSummary.session_id == session.id
    ).delete(synchronize_session=False)
    db.query(InterviewTurn).filter(
        InterviewTurn.session_id == session.id
    ).delete(synchronize_session=False)
    db.delete(session)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Live voice interview transport
# ---------------------------------------------------------------------------

@app.websocket("/interviews/{session_id}/voice")
async def interview_voice_stream(
    websocket: WebSocket,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Stream 16 kHz mono PCM utterances through the authenticated interview."""
    try:
        current_user = get_current_websocket_user(websocket, db)
    except HTTPException as exc:
        close_code = 4401 if exc.status_code == 401 else 1013
        await websocket.accept()
        await websocket.close(code=close_code, reason=str(exc.detail))
        return

    session = interview_service.get_owned_session(db, current_user.id, session_id)
    if session is None:
        await websocket.close(code=4404, reason="Interview not found")
        return
    if session.status != "active" or session.started_at is None:
        await websocket.close(code=4409, reason="Interview is not active")
        return

    await websocket.accept()
    deadline = time.monotonic() + session.duration_seconds
    audio_buffer = bytearray()
    answer_started: float | None = None
    question_text, question_category, difficulty = interview_service.next_question(
        db, session
    )

    async def send_question() -> None:
        await websocket.send_json({
            "type": "question",
            "text": question_text,
            "category": question_category,
            "difficulty": difficulty,
            "remaining_seconds": max(0, int(deadline - time.monotonic())),
        })
        if SPEECH_PROVIDER != "azure":
            return
        try:
            audio = await speech_service.synthesize(question_text)
        except speech_service.SpeechServiceUnavailable:
            return
        await websocket.send_bytes(audio)

    await websocket.send_json({
        "type": "ready",
        "session_id": str(session.id),
        "remaining_seconds": session.duration_seconds,
        "audio_input": (
            None
            if SPEECH_PROVIDER == "browser"
            else {
                "encoding": "pcm_s16le",
                "sample_rate_hz": 16000,
                "channels": 1,
            }
        ),
        "speech_provider": SPEECH_PROVIDER,
        "browser_voice_mode": SPEECH_PROVIDER == "browser",
    })
    await send_question()

    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                finished = interview_service.finish_session(db, session, "completed")
                interview_summary_service.create_or_update_summary(db, finished)
                await websocket.send_json({
                    "type": "ended",
                    "reason": "time_limit_reached",
                })
                await websocket.close(code=1000)
                return

            try:
                message = await asyncio.wait_for(
                    websocket.receive(), timeout=remaining
                )
            except asyncio.TimeoutError:
                finished = interview_service.finish_session(db, session, "completed")
                interview_summary_service.create_or_update_summary(db, finished)
                await websocket.send_json({
                    "type": "ended",
                    "reason": "time_limit_reached",
                })
                await websocket.close(code=1000)
                return

            if message.get("bytes") is not None:
                chunk = message["bytes"]
                if len(audio_buffer) + len(chunk) > MAX_INTERVIEW_AUDIO_BYTES:
                    await websocket.send_json({
                        "type": "error",
                        "code": "audio_too_large",
                        "message": "Answer audio exceeded the 10 MB limit",
                    })
                    audio_buffer.clear()
                    continue
                if answer_started is None:
                    answer_started = time.monotonic()
                audio_buffer.extend(chunk)
                continue

            text_message = message.get("text")
            if text_message is None:
                continue
            try:
                command = json.loads(text_message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "code": "invalid_message",
                    "message": "Messages must be valid JSON",
                })
                continue

            command_type = command.get("type")
            if command_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if command_type == "end":
                finished = interview_service.finish_session(db, session, "completed")
                interview_summary_service.create_or_update_summary(db, finished)
                await websocket.send_json({"type": "ended", "reason": "client"})
                await websocket.close(code=1000)
                return
            if command_type == "answer_start":
                answer_started = time.monotonic()
                continue
            if command_type == "answer_transcript":
                transcript = command.get("text")
                if not isinstance(transcript, str) or not transcript.strip():
                    await websocket.send_json({
                        "type": "error",
                        "code": "empty_transcript",
                        "message": "Send recognized speech in the text field",
                    })
                    continue
                try:
                    voice_metrics = voice_analysis_service.VoiceMetricsInput.model_validate(
                        command
                    )
                except ValueError:
                    voice_metrics = voice_analysis_service.VoiceMetricsInput()
                answer_duration_ms = (
                    int((time.monotonic() - answer_started) * 1000)
                    if answer_started is not None
                    else voice_metrics.duration_ms
                )
                voice_metrics.duration_ms = answer_duration_ms
                turn = interview_service.save_answer(
                    db,
                    session,
                    question_text,
                    question_category,
                    difficulty,
                    transcript.strip(),
                    answer_duration_ms,
                )
                voice = voice_analysis_service.save_voice_analysis(
                    db, session, turn, voice_metrics
                )
                audio = bytes(audio_buffer)
                audio_buffer.clear()
                if audio:
                    audio_analysis_queue.enqueue(
                        db, session, turn, voice, audio,
                        command.get("audio_content_type", "audio/webm"),
                    )
                await websocket.send_json({
                    "type": "transcript",
                    "turn_no": turn.turn_no,
                    "text": transcript.strip(),
                })
                await websocket.send_json({
                    "type": "voice_analysis",
                    "turn_no": turn.turn_no,
                    "speaking_rate_wpm": voice.speaking_rate_wpm if voice else None,
                    "filler_word_count": voice.filler_word_count if voice else 0,
                    "pause_count": voice.pause_count if voice else 0,
                    "fluency_score": voice.fluency_score if voice else None,
                    "clarity_score": voice.clarity_score if voice else None,
                    "pace_score": voice.pace_score if voice else None,
                    "confidence_score": voice.confidence_score if voice else None,
                    "pronunciation_status": (
                        voice.analysis_status if voice else "unavailable"
                    ),
                    "feedback": voice.voice_feedback if voice else "",
                })
                decision, (
                    question_text,
                    question_category,
                    difficulty,
                ) = adaptive_interviewer.choose_next(db, session, turn)
                answer_started = None
                await websocket.send_json({
                    "type": "evaluation",
                    "turn_no": turn.turn_no,
                    "score": decision.score if decision else None,
                    "feedback": turn.answer_feedback,
                    "adaptive": decision is not None,
                })
                await send_question()
                continue
            if command_type != "answer_end":
                await websocket.send_json({
                    "type": "error",
                    "code": "unsupported_command",
                    "message": "Use answer_end, end, or ping",
                })
                continue
            if not audio_buffer:
                await websocket.send_json({
                    "type": "error",
                    "code": "empty_answer",
                    "message": "Send PCM audio before answer_end",
                })
                continue

            audio = bytes(audio_buffer)
            audio_buffer.clear()
            try:
                transcript = await speech_service.transcribe(audio)
            except speech_service.SpeechServiceUnavailable as exc:
                await websocket.send_json({
                    "type": "error",
                    "code": "speech_unavailable",
                    "message": str(exc),
                })
                continue
            if not transcript:
                await websocket.send_json({
                    "type": "error",
                    "code": "speech_not_recognized",
                    "message": "No speech was recognized",
                })
                continue

            turn = interview_service.save_answer(
                db,
                session,
                question_text,
                question_category,
                difficulty,
                transcript,
                int((time.monotonic() - answer_started) * 1000)
                if answer_started is not None
                else 0,
            )
            voice = voice_analysis_service.save_voice_analysis(db, session, turn)
            audio_analysis_queue.enqueue(
                db, session, turn, voice, audio, "audio/raw"
            )
            await websocket.send_json({
                "type": "transcript",
                "turn_no": turn.turn_no,
                "text": transcript,
            })
            await websocket.send_json({
                "type": "voice_analysis",
                "turn_no": turn.turn_no,
                "speaking_rate_wpm": voice.speaking_rate_wpm if voice else None,
                "filler_word_count": voice.filler_word_count if voice else 0,
                "pause_count": voice.pause_count if voice else 0,
                "fluency_score": voice.fluency_score if voice else None,
                "clarity_score": voice.clarity_score if voice else None,
                "pace_score": voice.pace_score if voice else None,
                "confidence_score": voice.confidence_score if voice else None,
                "pronunciation_status": (
                    voice.analysis_status if voice else "unavailable"
                ),
                "feedback": voice.voice_feedback if voice else "",
            })
            decision, (
                question_text,
                question_category,
                difficulty,
            ) = adaptive_interviewer.choose_next(db, session, turn)
            answer_started = None
            await websocket.send_json({
                "type": "evaluation",
                "turn_no": turn.turn_no,
                "score": decision.score if decision else None,
                "feedback": turn.answer_feedback,
                "adaptive": decision is not None,
            })
            await send_question()
    except (WebSocketDisconnect, WebSocketDisconnected):
        if session.status == "active":
            interview_service.finish_session(db, session, "interrupted")


@app.post("/account/verification-email", status_code=202)
def request_verification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.email_verified:
        return {"message": "Email is already verified"}
    token = account_service.issue_email_verification(db, current_user)
    try:
        email_service.send_email(
            current_user.email,
            "Verify your InterviewIQ email",
            f"Use this verification token with POST /account/verify-email:\n\n{token}",
        )
    except email_service.EmailConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Email service is not configured",
        ) from exc
    return {"message": "Verification email sent"}


@app.post("/account/verify-email")
def verify_email(request: TokenRequest, db: Session = Depends(get_db)):
    if account_service.consume_email_verification(db, request.token) is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"message": "Email verified"}


@app.post("/account/password/change")
def change_password(
    request: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    current_user.password_hash = hash_password(request.password)
    current_user.password_changed_at = datetime.now(timezone.utc).replace(
        tzinfo=None
    )
    db.commit()
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return {"message": "Password changed; please log in again"}


@app.post("/account/password/reset/request", status_code=202)
def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    try:
        email_service.ensure_configured()
    except email_service.EmailConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Email service is not configured",
        ) from exc
    user = services_auth.get_user_by_email(db, request.email)
    if user is not None:
        token = account_service.issue_password_reset(db, user)
        try:
            email_service.send_email(
                user.email,
                "Reset your InterviewIQ password",
                f"Use this password-reset token with POST /account/password/reset/confirm:\n\n{token}",
            )
        except email_service.EmailConfigurationError as exc:
            raise HTTPException(
                status_code=503,
                detail="Email service is not configured",
            ) from exc
    return {"message": "If that email exists, reset instructions were sent"}


@app.post("/account/password/reset/confirm")
def confirm_password_reset(
    request: PasswordRequest,
    token: str = Query(..., min_length=32, max_length=256),
    db: Session = Depends(get_db),
):
    user = account_service.consume_password_reset(db, token)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.password_hash = hash_password(request.password)
    user.password_changed_at = datetime.now(timezone.utc).replace(
        tzinfo=None
    )
    db.commit()
    return {"message": "Password reset successfully"}


# ---------------------------------------------------------------------------
# Resume, job-description, and analysis workflows
# ---------------------------------------------------------------------------

@app.post("/analyze", response_model=AnalysisResponse)
def analyze(
    job_description: str | None = Form(
        None, description="Optional. Leave empty to use your latest saved one"
    ),
    resume: UploadFile | None = File(
        None, description="Optional, PDF only (max 5 MB). Leave empty to use your latest saved one"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Blank or Swagger's placeholder word counts as "not provided"
    raw_jd = (job_description or "").strip()
    jd_text: str | None = None if raw_jd.lower() in {"", "string"} else raw_jd

    resume_bytes: bytes | None = None
    original_filename: str | None = None

    # Only handle the file if the user actually chose one
    if resume is not None and resume.filename:
        suffix = Path(resume.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

        header = resume.file.read(5)
        resume.file.seek(0)
        if header != b"%PDF-":
            raise HTTPException(status_code=400, detail="File is not a valid PDF")

        resume_bytes = resume.file.read(MAX_UPLOAD_BYTES + 1)
        if len(resume_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Resume is too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
            )

        original_filename = resume.filename

    try:
        result = process_submission(
            db=db,
            user=current_user,
            resume_bytes=resume_bytes,
            original_filename=original_filename,
            job_description=jd_text,
        )
    except MissingInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidInputError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except AnalysisUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="Analysis service is busy. Please try again in a minute.",
        )
    return AnalysisResponse.model_validate(result["analysis"])


# ---------------------------------------------------------------------------
# Question generation and question-bank endpoints
# ---------------------------------------------------------------------------

@app.get("/questions/options", response_model=QuestionOptionsResponse)
def question_options(
    current_user: User = Depends(get_current_user),
):
    """Return question-generation options for the authenticated user."""
    return QuestionOptionsResponse(
        categories=[
            CategoryInfo(name=name, **info)
            for name, info in question_service.CATEGORY_INFO.items()
        ],
        difficulties=[
            DifficultyInfo(name=name, description=description)
            for name, description in question_service.DIFFICULTY_INFO.items()
        ],
        count_min=1,
        count_max=question_service.MAX_QUESTIONS,
        count_default=DEFAULT_QUESTION_COUNT,
    )


@app.post("/questions/generate", response_model=GenerateQuestionsResponse)
def generate_questions(
    payload: GenerateQuestionsRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create new interview questions from your saved resume and job description.

    Every question ever generated is remembered, so each call gives you NEW ones.
    You need to have used /analyze at least once, so a resume and a job description are saved.
    """
    payload = payload or GenerateQuestionsRequest()

    try:
        result = question_service.generate_questions(
            db,
            current_user,
            count=payload.count,
            categories=payload.categories,
            difficulty=payload.difficulty,
        )
    except MissingInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnalysisUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="Question service is busy. Please try again in a minute.",
        )

    return GenerateQuestionsResponse(
        batch_no=result["batch_no"],
        requested=result["requested"],
        saved=result["saved"],
        duplicates_skipped=result["duplicates_skipped"],
        total_questions=result["total_questions"],
        note=result["note"],
        questions=[QuestionOut.model_validate(q) for q in result["questions"]],
    )


@app.get("/questions", response_model=QuestionListResponse)
def list_questions(
    category: QuestionCategory | None = None,
    batch_no: int | None = Query(None, ge=1, description="Only this generation round"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every question generated for you so far, newest round first."""
    total, items = question_service.list_questions(
        db, current_user, category=category, batch_no=batch_no, limit=limit, offset=offset
    )

    return QuestionListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[QuestionOut.model_validate(q) for q in items],
    )
