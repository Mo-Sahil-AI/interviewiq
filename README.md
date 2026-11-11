# AI Resume Analyzer Backend

A FastAPI backend that lets a user create an account, upload a PDF resume, paste a job
description, and get AI feedback on how well the two match.

## Features

* **Accounts:** register, log in and log out. Passwords are hashed with Argon2id. The login
  token is a JWT kept in an HttpOnly cookie. Logging out cancels the token on the server
  (via Redis), so a copied cookie stops working immediately.
* **Version history:** every resume and job description is saved as a numbered version and
  fingerprinted with a hash. Submitting the same text again reuses the saved version, and the
  AI is not called twice for the same resume + job description pair.
* **PDF text extraction:** PDFs only, up to 5 MB. Scanned (image-only), corrupt and
  password-protected PDFs are rejected with a clear message.
* **AI analysis (Google Gemini):** returns an overview, how well the resume matches, content
  that is irrelevant to the job, missing requirements, suggestions, and extra details
  (strengths and matched keywords). If one Gemini model fails or returns unusable output, the
  next model is tried. If all fail, the API answers `503` instead of crashing.
* **Safe with double clicks:** two requests at the same moment cannot create duplicate versions.
* **Question generator:** creates interview questions from your saved resume and job description
  (and the analysis, if there is one). Every question is saved, and every new round is told what
  already exists, so it never repeats itself. Exact repeats, re-spaced copies and reworded copies
  are all thrown away. Choose how many (1-20), the categories (technical, behavioral, situational,
  resume_based, hr) and the difficulty, or leave them out for a balanced mix.
* **Interactive docs:** Swagger UI at `/docs`.

## Tech stack

FastAPI, SQLAlchemy 2 + PostgreSQL (psycopg 3), Redis, Google GenAI SDK, PyMuPDF.

## Prerequisites

* Python 3.10+
* PostgreSQL 17 or newer (the supplied `db_structure.sql` was made on PostgreSQL 18; on an
  older server, delete the line `SET transaction_timeout = 0;` from it first)
* Redis (used for logout)
* A Google Gemini API key

## Setup

**1. Create a virtual environment and install the packages**

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Create the database and its tables**

```bash
createdb your_db_name
psql -d your_db_name -f db_structure.sql
```

**3. Create a file named `.env` next to `main.py`**

```
DATABASE_URL=postgresql://username:password@localhost/your_db_name
SECRET_KEY=paste_a_long_random_string_here
GOOGLE_API_KEY=your_google_api_key_here

# optional
REDIS_URL=redis://localhost:6379/0
ACCESS_TOKEN_EXPIRE_MINUTES=2880
```

Generate a secret key with `openssl rand -hex 32`. Never commit `.env` to git.

**4. Start Redis and the server**

```bash
sudo service redis-server start      # or: redis-server
uvicorn main:app --reload
```

**5. Try it**

Open <http://127.0.0.1:8000/docs>, then:

1. `POST /register` to create an account.
2. `POST /login`. This sets your login cookie.
3. `POST /analyze` with a PDF resume and a job description. Leave either one empty to reuse
   the latest one you saved (a new user must provide both).
4. `GET /questions/options` (no login needed) to see what you can ask for: the five categories
   (`technical`, `resume_based`, `behavioral`, `situational`, `hr`, each with a description and an
   example), the three difficulty levels (`easy`, `medium`, `hard`) and how many questions you can
   request (1 to 20).
5. `POST /questions/generate` to get new interview questions. You need to have used `/analyze`
   first. Call it again for more: each round gives questions you have not seen. Send
   `{"count": 5, "categories": ["technical"], "difficulty": "hard"}` to choose, or send
   `{"count": 10}` for a balanced mix.
6. `GET /questions` to see every question so far (filters: `category`, `batch_no`, `limit`, `offset`).
7. `POST /logout` when you are done.

## Responses to know about

| Status | Meaning |
|---|---|
| 400 | Missing input (for example a new user sent no resume), or the file is not a PDF |
| 401 | Not logged in, or the session ended |
| 413 | Resume bigger than 5 MB |
| 422 | The PDF has no readable text, is corrupt or password-protected, or the text is too long |
| 503 | The AI service is unavailable. Try again in a minute |

Asking for questions before any resume and job description are saved gives `400`. A `count` outside
1-20 gives `422`.

## Updating an existing database

If your database was created before these versions, run the migrations once, **in order**
(each one is all-or-nothing and safe to repeat):

```bash
psql -d your_db_name -f migrations/001_enforce_not_null.sql
psql -d your_db_name -f migrations/002_add_questions.sql
psql -d your_db_name -f migrations/003_users_created_at_not_null.sql
```

* `001` makes `users.password_hash` and `resume_analysis.analysis_hash` required, as `models.py` expects.
* `002` adds the `questions` table. (The server also creates it by itself when it starts, so this
  only makes it explicit.)
* `003` makes `users.created_at` required, as `models.py` expects.

If a row blocks `001` or `003`, the script stops with a message and changes nothing.

## Tests

The tests use a fake Gemini, so they cost nothing and need no API key. They **empty the tables
they use**, so they only run against a database whose name ends in `_test`:

```bash
pip install -r requirements-dev.txt
createdb your_db_name_test
psql -d your_db_name_test -f db_structure.sql
TEST_DATABASE_URL=postgresql://username:password@localhost/your_db_name_test pytest -v
```

You should see `87 passed` (22 for the review fixes, 65 for the question generator).

Redis must be running for the logout test.

## Project files

| File | Purpose |
|---|---|
| `main.py` | API endpoints, upload limits, Swagger page |
| `services.py` | Resume and job description versions, PDF reading, Gemini call and its validation |
| `question_service.py` | Question generator: prompt, checking the AI's output, repeat protection, saving |
| `auth.py`, `services_auth.py` | Passwords, login tokens, logout, registration |
| `models.py`, `schemas.py`, `database.py` | Database tables, request/response shapes, connection |
| `db_structure.sql`, `migrations/` | Database structure and upgrade scripts |
| `test_fixes.py`, `test_questions.py`, `conftest.py`, `helpers.py` | Automated tests |

## Before you deploy

* In `main.py`, set `secure=True` on the login cookie (you need HTTPS).
* If Redis is down, logout cannot cancel tokens and the API lets requests through rather than
  locking everyone out. Watch for "Redis is unavailable" in the logs.
* Each `/questions/generate` call costs one AI request. There is no per-user limit yet, so add one before
  opening the app to the public.
* Not covered yet: rate limits per user, email verification and password reset.
