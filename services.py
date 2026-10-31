import uuid
from models import JobDescription
from sqlalchemy.orm import Session
from models import UserProfile
from models import ResumeAnalysis
import hashlib
import pymupdf
from sqlalchemy import desc
import os
import json

from google import genai
from dotenv import load_dotenv
from models import Resume



class AnalysisUnavailableError(Exception):
    pass


class MissingInputError(Exception):
    pass

def generate_hash(text: str):

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def get_latest_resume(
        db: Session,
        user_id
):

    return (
        db.query(Resume)
        .filter(
            Resume.user_id == user_id
        )
        .order_by(
            desc(Resume.version_no)
        )
        .first()
    )


def resume_changed(
        db: Session,
        user_id,
        new_resume_hash
):

    latest_resume = get_latest_resume(
        db,
        user_id
    )

    if latest_resume is None:
        return True

    return (
        latest_resume.resume_hash
        != new_resume_hash
    )


def create_resume_version(
        db: Session,
        user_id,
        file_name,
        resume_text
):

    latest_resume = get_latest_resume(
        db,
        user_id
    )

    if latest_resume:

        next_version = (
            latest_resume.version_no + 1
        )

    else:

        next_version = 1

    resume_hash = generate_hash(
        resume_text
    )

    resume = Resume(
        id=uuid.uuid4(),

        user_id=user_id,

        version_no=next_version,

        file_name=file_name,

        resume_text=resume_text,

        resume_hash=resume_hash
    )

    db.add(resume)

    db.commit()

    db.refresh(resume)

    return resume



def create_resume_if_changed(
        db,
        user_id,
        file_name,
        resume_text
):

    resume_hash = generate_hash(
        resume_text
    )

    latest_resume = get_latest_resume(
        db,
        user_id
    )

    # First Resume
    if latest_resume is None:

        resume = create_resume_version(
            db,
            user_id,
            file_name,
            resume_text
        )

        update_current_resume(
            db,
            user_id,
            resume
        )

        return resume

    # Same Resume
    existing_hash = str(
        latest_resume.resume_hash
    )

    if existing_hash == resume_hash:

        update_current_resume(
            db,
            user_id,
            latest_resume
        )

        return latest_resume

    # Changed Resume

    resume = create_resume_version(
        db,
        user_id,
        file_name,
        resume_text
    )

    update_current_resume(
        db,
        user_id,
        resume
    )

    return resume

def get_latest_jd(
        db,
        user_id
):

    return (
        db.query(JobDescription)
        .filter(
            JobDescription.user_id == user_id
        )
        .order_by(
            JobDescription.version_no.desc()
        )
        .first()
    )


def create_jd_version(
        db,
        user_id,
        job_description
):

    latest_jd = get_latest_jd(
        db,
        user_id
    )

    if latest_jd:

        next_version = (
            latest_jd.version_no + 1
        )

    else:

        next_version = 1

    jd_hash = generate_hash(
        job_description
    )

    jd = JobDescription(
        id=uuid.uuid4(),

        user_id=user_id,

        version_no=next_version,

        job_description=job_description,

        jd_hash=jd_hash
    )

    db.add(jd)

    db.commit()

    db.refresh(jd)

    return jd


def create_jd_if_changed(
        db,
        user_id,
        job_description
):

    jd_hash = generate_hash(
        job_description
    )

    latest_jd = get_latest_jd(
        db,
        user_id
    )

    # First JD
    if latest_jd is None:

        jd = create_jd_version(
            db,
            user_id,
            job_description
        )

        update_current_jd(
            db,
            user_id,
            jd
        )

        return jd

    # Same JD

    if latest_jd.jd_hash == jd_hash:

        update_current_jd(
            db,
            user_id,
            latest_jd
        )

        return latest_jd

    # Changed JD

    jd = create_jd_version(
        db,
        user_id,
        job_description
    )

    update_current_jd(
        db,
        user_id,
        jd
    )

    return jd
def get_user_profile(
        db,
        user_id
):

    return (
        db.query(UserProfile)
        .filter(
            UserProfile.user_id == user_id
        )
        .first()
    )


def create_user_profile(
        db,
        user_id
):

    profile = UserProfile(
        user_id=user_id
    )

    db.add(profile)

    db.commit()

    db.refresh(profile)

    return profile


def get_or_create_profile(
        db,
        user_id
):

    profile = get_user_profile(
        db,
        user_id
    )

    if profile:
        return profile

    return create_user_profile(
        db,
        user_id
    )


def update_current_resume(
        db,
        user_id,
        resume
):

    profile = get_or_create_profile(
        db,
        user_id
    )

    profile.current_resume_id = resume.id

    profile.current_resume_version = (
        resume.version_no
    )

    db.commit()

    db.refresh(profile)

    return profile


def update_current_jd(
        db,
        user_id,
        jd
):

    profile = get_or_create_profile(
        db,
        user_id
    )

    profile.current_jd_id = jd.id

    profile.current_jd_version = (
        jd.version_no
    )

    db.commit()

    db.refresh(profile)

    return profile


def generate_analysis_hash(
        resume_hash,
        jd_hash
):

    combined = (
        resume_hash +
        jd_hash
    )

    return hashlib.sha256(
        combined.encode()
    ).hexdigest()


def get_latest_analysis(
        db,
        user_id
):

    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.user_id == user_id
        )
        .order_by(
            ResumeAnalysis.analysis_version.desc()
        )
        .first()
    )


def get_analysis_by_hash(
        db,
        user_id,
        analysis_hash
):

    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.user_id == user_id,
            ResumeAnalysis.analysis_hash
            == analysis_hash
        )
        .first()
    )


def create_analysis(
        db,
        user_id,
        resume,
        jd
):

    analysis_hash = generate_analysis_hash(
        resume.resume_hash,
        jd.jd_hash
    )

    existing = get_analysis_by_hash(
    db,
    user_id,
    analysis_hash
)

    if existing:

        update_current_analysis(
            db,
            user_id,
            existing
        )

        return existing

    latest = get_latest_analysis(
        db,
        user_id
    )

    if latest:

        next_version = (
            latest.analysis_version + 1
        )

    else:

        next_version = 1

    analysis_result = (
        generate_resume_analysis(
            resume.resume_text,
            jd.job_description
        )
    )

    analysis = ResumeAnalysis(

        id=uuid.uuid4(),

        user_id=user_id,

        analysis_version=next_version,

        resume_id=resume.id,

        jd_id=jd.id,

        resume_version=resume.version_no,

        jd_version=jd.version_no,

        overview=analysis_result["overview"],

        match_analysis=analysis_result[
            "match_analysis"
        ],

        irrelevant_content=analysis_result[
            "irrelevant_content"
        ],

        missing_requirements=analysis_result[
            "missing_requirements"
        ],

        suggestions=analysis_result[
            "suggestions"
        ],

        others=analysis_result[
            "others"
        ],

        analysis_hash=analysis_hash
    )

    db.add(analysis)

    db.commit()

    db.refresh(analysis)

    update_current_analysis(
        db,
        user_id,
        analysis
    )

    return analysis



def update_current_analysis(
        db,
        user_id,
        analysis
):

    profile = get_or_create_profile(
        db,
        user_id
    )

    profile.current_analysis_id = (
        analysis.id
    )

    profile.current_analysis_version = (
        analysis.analysis_version
    )

    db.commit()

    db.refresh(profile)

    return profile

def extract_resume_text(pdf_path):

    text: str = ""

    with pymupdf.open(pdf_path) as document:

        for page in document:

            page_text = str(page.get_text("text"))

            text += page_text

    return text.strip()


load_dotenv()

api_key = os.getenv(
    "GOOGLE_API_KEY"
)

client = None

if api_key:
    client = genai.Client(
        api_key=api_key
    )

def generate_resume_analysis(
        resume_text: str,
        job_description: str
):

    if client is None:
        raise ValueError(
            "Gemini client not initialized"
        )

    prompt = f"""
You are an expert technical recruiter.

Analyze the resume against the job description.

Return ONLY a valid JSON object.

Do not use markdown.

Do not use triple backticks.

Do not add explanations.

Do not add text before or after the JSON.

Return this exact structure:

{{
    "overview": "",
    "match_analysis": "",
    "irrelevant_content": "",
    "missing_requirements": "",
    "suggestions": "",
    "others": {{
        "strengths": [],
        "keywords_matched": []
    }}
}}

Resume:

{resume_text}

Job Description:

{job_description}
"""

    MODELS = [

        "models/gemini-flash-lite-latest",

        "models/gemini-3.1-flash-lite",

        "models/gemini-3.5-flash"

    ]

    response = None

    last_error = None

    for model_name in MODELS:

        print(
            f"Trying model: {model_name}"
        )

        try:

            response = (
                client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
            )

            print(
                f"Success: {model_name}"
            )

            break

        except Exception as e:

            print(
                f"Failed: {model_name}"
            )

            print(e)

            last_error = e

    if response is None:

        raise RuntimeError(
            f"All Gemini models failed: {last_error}"
        )

    if not response.text:

        raise ValueError(
            "Gemini returned empty response"
        )

    cleaned = (
        response.text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1:

        cleaned = cleaned[
            start:end + 1
        ]

    try:

        return json.loads(
            cleaned
        )

    except json.JSONDecodeError:

        print(
            "\nInvalid JSON Returned:\n"
        )

        print(cleaned)

        raise


def process_submission(
        db,
        user,
        resume_file_path=None,
        original_filename=None,
        job_description=None
):

    latest_resume = get_latest_resume(
        db,
        user.id
    )

    latest_jd = get_latest_jd(
        db,
        user.id
    )

    # New users must give both inputs.
    # Old users can skip an input if something is already saved.
    missing = []

    if not resume_file_path and latest_resume is None:
        missing.append("a resume")

    if not job_description and latest_jd is None:
        missing.append("a job description")

    if missing:
        raise MissingInputError(
            "Please provide "
            + " and ".join(missing)
            + "."
        )

    # Fill in any missing input with the saved text
    if resume_file_path:

        resume_text = extract_resume_text(
            resume_file_path
        )

        file_name = original_filename or "resume.pdf"

    else:

        assert latest_resume is not None

        resume_text = str(latest_resume.resume_text)

        file_name = str(latest_resume.file_name)

    if not job_description:

        assert latest_jd is not None

        job_description = str(latest_jd.job_description)

    # Same text gives the same hash, so no new version is created
    resume = create_resume_if_changed(
        db,
        user.id,
        file_name,
        resume_text
    )

    jd = create_jd_if_changed(
        db,
        user.id,
        job_description
    )

    analysis = create_analysis(
        db,
        user.id,
        resume,
        jd
    )

    return {
        "user": user,
        "resume": resume,
        "jd": jd,
        "analysis": analysis
    }