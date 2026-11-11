import logging
import uuid
from pathlib import Path

from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile
)
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    create_access_token,
    get_current_user,
    revoke_token,
)
from database import Base, engine, get_db
from models import User
from schemas import (
    DEFAULT_QUESTION_COUNT,
    AnalysisResponse,
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
)
import question_service
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

Base.metadata.create_all(bind=engine)

app = FastAPI()

MAX_UPLOAD_BYTES = 5 * 1024 * 1024                 # 5 MB resume
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 256 * 1024  # + job description and form overhead


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


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}


@app.post("/register", response_model=RegisterResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, request.email, request.password)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="Email already registered")

    return {"message": "User registered successfully", "email": user.email}


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
        secure=False,     # change to True when you deploy with HTTPS
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
        revoke_token(token)

    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return {"message": "Logged out"}


def save_upload_limited(upload: UploadFile, destination: Path, limit: int) -> None:
    """Copy an upload to disk; stop and clean up if it is bigger than `limit` bytes."""
    written = 0
    try:
        with open(destination, "wb") as out:
            while chunk := upload.file.read(1024 * 1024):
                written += len(chunk)
                if written > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Resume is too large (max {limit // (1024 * 1024)} MB).",
                    )
                out.write(chunk)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


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

    file_path: Path | None = None
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

        file_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"
        save_upload_limited(resume, file_path, MAX_UPLOAD_BYTES)

        original_filename = resume.filename

    try:
        result = process_submission(
            db=db,
            user=current_user,
            resume_file_path=str(file_path) if file_path else None,
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
    finally:
        if file_path:
            file_path.unlink(missing_ok=True)

    return AnalysisResponse.model_validate(result["analysis"])


@app.get("/questions/options", response_model=QuestionOptionsResponse)
def question_options():
    """What you can ask for when generating questions: every category (with a description and
    an example), the difficulty levels, and the allowed number of questions. No login needed."""
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
