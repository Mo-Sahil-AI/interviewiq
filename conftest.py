"""
Shared test setup.

SAFE BY DESIGN: the tests EMPTY the tables they use, so they refuse to run unless
TEST_DATABASE_URL points at a database whose name ends in "_test".

    createdb resume_analyzer_test
    psql -d resume_analyzer_test < db_structure.sql
    TEST_DATABASE_URL=postgresql://user:pass@localhost/resume_analyzer_test pytest -v

Gemini is replaced by a fake, so no API key or money is needed.
Redis must be running (it is used for logout).
"""
import os

import pytest

_URL = os.getenv("TEST_DATABASE_URL", "")
_DBNAME = _URL.rsplit("/", 1)[-1].split("?")[0]
if not _URL or not _DBNAME.endswith("_test"):
    raise RuntimeError(
        "Set TEST_DATABASE_URL to a database whose name ends with '_test'. "
        "These tests wipe the tables, so they never run on your real database."
    )
os.environ["DATABASE_URL"] = _URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only-0123456789abcdef")
os.environ.setdefault("GOOGLE_API_KEY", "dummy-key")

from fastapi.testclient import TestClient  # noqa: E402

import database  # noqa: E402
import main  # noqa: E402
import services  # noqa: E402
from helpers import GOOD, FakeGemini  # noqa: E402
import json  # noqa: E402


@pytest.fixture
def gemini(monkeypatch):
    """gemini(behaviour) installs a fake AI and returns it (see FakeGemini)."""
    def install(behaviour=lambda n: json.dumps(GOOD)):
        fake = FakeGemini(behaviour)
        monkeypatch.setattr(services, "client", fake)
        return fake
    return install


@pytest.fixture(autouse=True)
def clean_db():
    with database.engine.begin() as conn:
        conn.exec_driver_sql(
            "TRUNCATE users, resumes, job_descriptions, resume_analysis, user_profile, questions CASCADE")
    yield


@pytest.fixture
def client():
    return TestClient(main.app, raise_server_exceptions=False)
