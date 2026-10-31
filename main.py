import shutil
import uuid
from pathlib import Path

from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
)
from sqlalchemy.orm import Session
from services import (
    AnalysisUnavailableError,
    MissingInputError,
    process_submission,
)

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    create_access_token,
    get_current_user,
)
from database import Base, engine, get_db
from models import User
from schemas import LoginRequest, RegisterRequest, RegisterResponse
from services import process_submission
from services_auth import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()


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
def logout(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return {"message": "Logged out"}


@app.post("/analyze")
def analyze(
    job_description: str | None = Form(
        None, description="Optional. Leave empty to use your latest saved one"
    ),
    resume: UploadFile | None = File(
        None, description="Optional, PDF only. Leave empty to use your latest saved one"
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
        with open(file_path, "wb") as f:
            shutil.copyfileobj(resume.file, f)

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
    except AnalysisUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="Analysis service is busy. Please try again in a minute.",
        )
    finally:
        if file_path:
            file_path.unlink(missing_ok=True)

    analysis = result["analysis"]

    return {
        "analysis_version": analysis.analysis_version,
        "resume_version": analysis.resume_version,
        "jd_version": analysis.jd_version,
        "overview": analysis.overview,
        "match_analysis": analysis.match_analysis,
        "missing_requirements": analysis.missing_requirements,
        "suggestions": analysis.suggestions,
    }