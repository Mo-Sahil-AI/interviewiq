from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def add_slide(prs, title, bullets, notes=""):
    slide_layout = prs.slide_layouts[1] # Title and Content
    slide = prs.slides.add_slide(slide_layout)
    
    # Set Title
    title_shape = slide.shapes.title
    title_shape.text = title
    title_shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(30, 58, 138) # Dark Blue
    title_shape.text_frame.paragraphs[0].font.size = Pt(32)
    title_shape.text_frame.paragraphs[0].font.bold = True

    # Set Content
    body_shape = slide.placeholders[1]
    tf = body_shape.text_frame
    tf.text = "" # Clear default text
    
    for bullet in bullets:
        p = tf.add_paragraph()
        p.text = bullet
        p.level = 0
        p.font.size = Pt(18)
        p.space_after = Pt(10)

    # Set Notes
    if notes:
        notes_slide = slide.notes_slide
        text_frame = notes_slide.notes_text_frame
        text_frame.text = notes

# Initialize Presentation
prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

# --- SLIDE 1: Title ---
slide_layout = prs.slide_layouts[0] # Title Slide
slide = prs.slides.add_slide(slide_layout)
slide.shapes.title.text = "InterviewIQ"
slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = RGBColor(30, 58, 138)
slide.placeholders[1].text = "AI Interview Chat Assistant\nTeam ML Quad | SparkX 3.0 Innovation Challenge"

# --- SLIDE 2: Problem & Solution ---
add_slide(prs, "The Problem & Our Solution", [
    "The Problem: Generic question banks lack context. Text-only tools don't measure vocal delivery. Human coaching is expensive.",
    "The Solution: InterviewIQ provides context-aware AI gap analysis (Resume vs. JD).",
    "Features: Live, voice-enabled mock interviews with real-time adaptation.",
    "Outcome: Quantifiable delivery metrics and a personalized coaching chatbot."
], "Speaker Notes: Welcome. Current tools are either generic text banks or expensive human coaches. InterviewIQ bridges this gap by analyzing your specific resume against a job description, then conducting a live voice interview that adapts to your answers in real-time.")

# --- SLIDE 3: Architecture ---
add_slide(prs, "System Architecture & Entry Point", [
    "Files: main.py, config.py, database.py, requirements.txt",
    "main.py: FastAPI entry point. Handles routing, security middleware, and upload limits.",
    "config.py: Centralized environment configuration (DB URLs, API keys, Redis).",
    "database.py: SQLAlchemy engine and session management.",
    "requirements.txt: Strictly pinned dependencies (FastAPI 0.162, SQLAlchemy 2.1, PyMuPDF)."
], "Speaker Notes: The backend is built on FastAPI. main.py orchestrates all HTTP and WebSocket routes. We use config.py to manage environment variables securely, and database.py handles our SQLAlchemy connections.")

# --- SLIDE 4: Data Modeling ---
add_slide(prs, "Data Modeling & Schema Design", [
    "Files: models.py, schemas.py, db_structure.sql",
    "models.py: 11 SQLAlchemy ORM tables (Users, Resumes, Questions, Sessions). Uses UUIDs.",
    "schemas.py: Pydantic models for strict request/response validation.",
    "db_structure.sql: Foundational PostgreSQL schema with advanced partial unique indexes."
], "Speaker Notes: Data integrity is crucial. models.py defines our 11 tables using SQLAlchemy 2.0 syntax. We use Pydantic in schemas.py to validate every API request. Our database schema uses advanced features like partial indexes to enforce business logic at the database level.")

# --- SLIDE 5: Core AI Engine ---
add_slide(prs, "Core AI & Document Processing", [
    "Files: services.py, helpers.py",
    "PDF Extraction: Uses PyMuPDF to extract text in-memory. Rejects scanned/corrupt PDFs.",
    "Idempotent Versioning: SHA-256 hashing of documents. Identical uploads reuse existing records to save AI costs.",
    "AI Fallback: Iterates through 3 Gemini models. Returns 503 only if all fail."
], "Speaker Notes: In services.py, we handle PDF extraction and AI analysis. A key feature is our idempotent versioning: we hash the resume text. If a user uploads the same file twice, we skip the AI call, saving costs. We also implement a 3-model fallback for Gemini.")

# --- SLIDE 6: Question Generation ---
add_slide(prs, "Adaptive Question Generation", [
    "File: question_service.py",
    "Prompt Engineering: Injects resume, JD, and up to 150 past questions to prevent repetition.",
    "3-Layer Deduplication: 1. Prompt instructions. 2. Jaccard similarity check (>0.6 = drop). 3. Database ON CONFLICT DO NOTHING.",
    "Concurrency: Uses PostgreSQL advisory locks to serialize batch generation per user."
], "Speaker Notes: question_service.py ensures users never get the same question twice. We use a 3-layer deduplication strategy: prompt context, mathematical Jaccard similarity checking in Python, and database-level conflict resolution.")

# --- SLIDE 7: Mock Interview Lifecycle ---
add_slide(prs, "Voice Mock Interview Lifecycle", [
    "Files: interview_service.py, interview_summary_service.py",
    "State Machine: Sessions transition from preparing -> active -> completed/interrupted/failed.",
    "Snapshotting: Locks the specific resume/JD versions at session creation for consistency.",
    "Summarization: Aggregates turn scores, identifies strong/weak areas, and generates a final text summary."
], "Speaker Notes: The interview engine is managed in interview_service.py. It acts as a strict state machine. When an interview starts, it snapshots the exact resume and job description versions used. Upon finishing, interview_summary_service.py aggregates all the data to generate a comprehensive performance report.")

# --- SLIDE 8: The Adaptive Interviewer ---
add_slide(prs, "The Adaptive Interviewer (The 'Brain')", [
    "File: adaptive_interviewer.py",
    "Real-time Evaluation: After every answer, the AI scores it (0-100) and provides specific feedback.",
    "Dynamic Selection: Chooses the next category, difficulty, and target skill based on user strengths/gaps.",
    "Graceful Degradation: If the AI fails mid-interview, it falls back to the next saved question."
], "Speaker Notes: This is the brain of the operation: adaptive_interviewer.py. After every spoken answer, it evaluates the response and dynamically selects the next question. If the user answers well, it increases difficulty; if they struggle, it probes the gap.")

# --- SLIDE 9: Voice Analysis ---
add_slide(prs, "Voice Analysis & Metrics Pipeline", [
    "Files: voice_analysis_service.py, speech_service.py",
    "Deterministic Metrics: Calculates WPM, Fluency, Clarity, Grammar, and Pace without extra AI costs.",
    "Speech Integration: speech_service.py handles Browser Web Speech API (zero cost) and optional Azure Speech."
], "Speaker Notes: To measure delivery, voice_analysis_service.py calculates deterministic metrics like Words Per Minute, fluency, and filler word counts. This is done locally and instantly. speech_service.py manages the integration with the browser's native Web Speech API.")

# --- SLIDE 10: Async Pronunciation ---
add_slide(prs, "Asynchronous Pronunciation Scoring", [
    "Files: audio_analysis_queue.py, pronunciation_worker.py",
    "The Challenge: Browser STT doesn't expose phonemes for pronunciation scoring.",
    "The Solution: Audio chunks are pushed to a Redis queue (audio_analysis_queue.py).",
    "Background Worker: pronunciation_worker.py consumes the queue, runs the wav2vec2 model locally, and updates the DB asynchronously."
], "Speaker Notes: Accurate pronunciation scoring requires phoneme analysis, which browsers don't provide. To solve this without blocking the live interview, we push audio chunks to a Redis queue. A background script, pronunciation_worker.py, processes these using a local wav2vec2 model.")

# --- SLIDE 11: Coaching Assistant ---
add_slide(prs, "Personalized Coaching Assistant", [
    "File: assistant_service.py",
    "Context Assembly: Dynamically gathers the user's resume, JD, gap analysis, and interview history.",
    "Grounded Generation: Prompts the LLM to answer ONLY using the provided context, preventing hallucinations.",
    "Persistence: Chat history is saved and included in account exports/deletions."
], "Speaker Notes: Beyond the mock interview, users have a personalized coach. assistant_service.py builds a rich context window from the user's specific data before querying the AI. This ensures the assistant gives grounded, relevant advice rather than generic hallucinations.")

# --- SLIDE 12: Security & Auth ---
add_slide(prs, "Security, Auth & Account Management", [
    "Files: auth.py, services_auth.py, account_service.py, email_service.py",
    "Authentication: Argon2id password hashing. JWT in HttpOnly cookies.",
    "Session Revocation: Redis-backed token blacklist for instant logout.",
    "Data Sovereignty: account_service.py handles full data export and irreversible cascading deletion.",
    "Email Flows: email_service.py handles secure, time-limited password resets via SMTP."
], "Speaker Notes: Security is paramount. We use Argon2id for passwords and HttpOnly JWTs. Crucially, logout instantly revokes the token via Redis. account_service.py ensures data sovereignty, allowing users to export or permanently delete all their data.")

# --- SLIDE 13: Frontend & Deployment ---
add_slide(prs, "Frontend & Deployment", [
    "Files: static/ directory, run_interview.sh, .gitignore",
    "Frontend: Vanilla JavaScript (static/app.*, static/interview.*). Lightweight, no build step, fast load times.",
    "Deployment: run_interview.sh orchestrates the API server and the pronunciation worker simultaneously.",
    "Security: .gitignore ensures .env files and local databases are never committed."
], "Speaker Notes: The frontend is built with vanilla JavaScript in the static folder, ensuring lightning-fast load times with no complex build steps. Deployment is simplified via run_interview.sh, which starts both the API and the background worker.")

# --- SLIDE 14: Testing ---
add_slide(prs, "Testing & Quality Assurance", [
    "Files: conftest.py, test_fixes.py, test_questions.py",
    "Mock AI: Tests use a fake Gemini client, running at zero cost and zero latency.",
    "Isolation: Tests run against a dedicated _test database, truncating only relevant tables.",
    "CI/CD: GitHub Actions run the full suite on every push/PR."
], "Speaker Notes: Quality is ensured through a robust test suite. We use a mock AI client in our tests, meaning our CI pipeline runs instantly and costs nothing. Tests are strictly isolated to a dedicated test database, and GitHub Actions automatically runs them on every code change.")

# --- SLIDE 15: Conclusion ---
add_slide(prs, "Conclusion & Future Scope", [
    "Summary: Delivered a production-ready, secure, and highly optimized AI interview platform in 30 days.",
    "Future Scope: Alembic for automated DB migrations.",
    "Future Scope: Rate limiting and per-user AI quotas.",
    "Future Scope: Multi-language support and advanced prosody analysis.",
    "Future Scope: Dockerized deployment for one-click setup."
], "Speaker Notes: In 30 days, we built a fully functional, secure, and optimized AI interview platform. Moving forward, we plan to add automated migrations, rate limiting, and multi-language support. Thank you for your time. We are now open for questions.")

# Save the presentation
prs.save('InterviewIQ_Presentation.pptx')
print("Presentation generated successfully: InterviewIQ_Presentation.pptx")