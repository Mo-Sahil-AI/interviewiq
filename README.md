# AI Resume Analyzer Backend

This repository contains the backend code for an AI-powered resume analysis tool. It allows users to securely create an account, upload their resume, and compare it against a job description to get tailored AI feedback.

## 🌟 Features

* **Secure Authentication:** User registration, login, and logout functionalities using JWT (JSON Web Tokens) stored securely in cookies[cite: 3, 5]. Passwords are safely hashed using Argon2id[cite: 3].
* **Smart Version Control:** The database tracks and hashes different versions of your resumes and job descriptions. If you upload the same document twice, it smartly reuses the saved version instead of recreating it[cite: 6, 9].
* **PDF Text Extraction:** Extracts text directly from uploaded PDF resumes[cite: 5, 9].
* **AI-Powered Insights:** Connects to Google's Gemini AI to compare your resume against a job description, returning actionable insights like missing requirements, strengths, and improvement suggestions[cite: 9].
* **Interactive API Docs:** Includes a customized Swagger UI to easily test endpoints and upload files directly from your browser.

## 🛠️ Tech Stack

* **Framework:** FastAPI[cite: 5, 7]
* **Database:** SQLAlchemy with PostgreSQL (using psycopg)[cite: 4, 6, 7]
* **AI Integration:** Google GenAI SDK[cite: 7, 9]
* **PDF Processing:** PyMuPDF[cite: 7, 9]

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.10+**
* **PostgreSQL** (or another supported SQL database)
* A **Google Gemini API Key**

## 🚀 How to Setup and Save the Project

**1. Clone the repository (or create the files)**
If you haven't already, create a folder for your project and add all the provided Python files (`main.py`, `models.py`, `auth.py`, etc.) and the `requirements.txt` file into it.

**2. Create a Virtual Environment**
It is best practice to keep your project dependencies isolated. Run this in your terminal:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate


# Your database connection string
DATABASE_URL=postgresql://username:password@localhost/your_db_name

# A random secret string for securing user sessions (e.g., generate one using openssl rand -hex 32)
SECRET_KEY=your_super_secret_random_string

# Your Google Gemini API key for the AI analysis
GOOGLE_API_KEY=your_google_api_key_here




# How to run 
uvicorn main:app --reload


2. Test the API
Once the server is running, open your web browser and navigate to:
👉 http://127.0.0.1:8000/docsThis will open the interactive Swagger Dashboard where you can:Use the /register endpoint to create an account.   Use the /login endpoint to sign in (this will set your secure access cookie).   Use the /analyze endpoint to upload your PDF resume and paste a job description to see the AI's feedback.


Recreate the Database
When setting up on a new machine or environment, use the generated file to recreate the database structure:

psql -U your_postgres_username -h localhost -d your_new_database_name < db_structure.sql  