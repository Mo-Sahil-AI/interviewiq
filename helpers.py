"""Plain helpers shared by the test files. (The fixtures live in conftest.py.)"""
import inspect
import json
from types import SimpleNamespace

import pymupdf

import database

PASSWORD = "correct horse battery"
JD = "Backend Engineer. Required: Python, SQL, AWS. Preferred: Kubernetes."
GOOD = {
    "overview": "Solid backend profile.",
    "match_analysis": "Python and SQL match well.",
    "irrelevant_content": "Hobby game project.",
    "missing_requirements": "AWS, Kubernetes.",
    "suggestions": "Add an AWS project.",
    "others": {"strengths": ["Python"], "keywords_matched": ["SQL"]},
}


class FakeGemini:
    """Stands in for google.genai.Client.

    `behaviour` returns the reply text (or raises). It may take one argument, the call
    number, or two: the call number and the prompt that was sent.
    """

    def __init__(self, behaviour):
        self.calls = []
        self.models = SimpleNamespace(generate_content=self._generate)
        self._behaviour = behaviour
        self._takes_prompt = len(inspect.signature(behaviour).parameters) >= 2

    def _generate(self, model, contents, config=None):
        self.calls.append({"model": model, "contents": contents, "config": config})
        number = len(self.calls)
        text = self._behaviour(number, contents) if self._takes_prompt else self._behaviour(number)
        return SimpleNamespace(text=text)


def make_pdf(text="Asha Verma. Backend developer with three years of Python, Flask and SQL. " * 5) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(40, 40, 550, 800), text)
    return doc.tobytes()


def make_scanned_pdf() -> bytes:
    """A PDF that is only a picture - there is no text to extract."""
    doc = pymupdf.open()
    page = doc.new_page()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 200), False)
    pix.clear_with(200)
    page.insert_image(page.rect, pixmap=pix)
    return doc.tobytes()


def login(client, email="asha@example.com"):
    assert client.post("/register", json={"email": email, "password": PASSWORD}).status_code == 201
    assert client.post("/login", json={"email": email, "password": PASSWORD}).status_code == 200


def analyze(client, pdf=None, jd=JD):
    files = {"resume": ("cv.pdf", pdf if pdf is not None else make_pdf(), "application/pdf")}
    return client.post("/analyze", data={"job_description": jd}, files=files)


def count(table):
    with database.engine.connect() as conn:
        return conn.exec_driver_sql(f"SELECT count(*) FROM {table}").scalar()


# ---- helpers for the question tests --------------------------------------
def q(text, category="technical", difficulty="medium", skill="Python", points=None):
    """One question as the AI would send it."""
    return {
        "category": category,
        "difficulty": difficulty,
        "target_skill": skill,
        "question_text": text,
        "ideal_answer_points": points if points is not None else ["Explains the idea", "Gives an example"],
    }


def question_ai(*batches):
    """A fake AI: analysis requests get GOOD, each question request gets the next batch
    (the last batch repeats if there are more requests than batches)."""
    queue = list(batches)

    def behaviour(number, prompt):
        if "EARLIER QUESTIONS" in prompt:
            batch = queue.pop(0) if len(queue) > 1 else queue[0]
            return json.dumps({"questions": batch})
        return json.dumps(GOOD)

    return behaviour
