import uuid
from datetime import datetime
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterResponse(BaseModel):
    message: str
    email: EmailStr


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analysis_version: int
    resume_version: int
    jd_version: int
    overview: str | None = None
    match_analysis: str | None = None
    irrelevant_content: str | None = None
    missing_requirements: str | None = None
    suggestions: str | None = None
    others: dict | None = None      # {"strengths": [...], "keywords_matched": [...]}


QuestionCategory = Literal["technical", "behavioral", "situational", "resume_based", "hr"]
QuestionDifficulty = Literal["easy", "medium", "hard"]


DEFAULT_QUESTION_COUNT = 10

_CATEGORY_NAMES = ", ".join(get_args(QuestionCategory))
_DIFFICULTY_NAMES = ", ".join(get_args(QuestionDifficulty))


class GenerateQuestionsRequest(BaseModel):
    # The FIRST example is what Swagger pre-fills, so it is the balanced mix (no filters).
    model_config = ConfigDict(json_schema_extra={"examples": [
        {"count": DEFAULT_QUESTION_COUNT},
        {"count": 5, "categories": ["technical", "behavioral"], "difficulty": "medium"},
        {"count": 3, "categories": ["resume_based"]},
    ]})

    count: int = Field(
        DEFAULT_QUESTION_COUNT, ge=1, le=20,
        description="How many NEW questions to create (1-20)",
    )
    categories: list[QuestionCategory] | None = Field(
        None,
        description=f"Any of: {_CATEGORY_NAMES}. Leave out for a balanced mix of all categories. "
                    "See GET /questions/options for what each one means.",
    )
    difficulty: QuestionDifficulty | None = Field(
        None,
        description=f"One of: {_DIFFICULTY_NAMES}. Leave out for a mix of all levels.",
    )


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_no: int
    item_no: int
    category: str
    difficulty: str
    target_skill: str | None = None
    question_text: str
    ideal_answer_points: list[str] | None = None
    resume_version: int
    jd_version: int
    created_at: datetime | None = None


class GenerateQuestionsResponse(BaseModel):
    batch_no: int | None = None          # None when nothing new could be created
    requested: int
    saved: int
    duplicates_skipped: int              # repeats of earlier questions that were thrown away
    total_questions: int                 # all questions you have so far
    note: str | None = None
    questions: list[QuestionOut]


class QuestionListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[QuestionOut]


class CategoryInfo(BaseModel):
    name: QuestionCategory          # the value to send
    label: str                      # a friendly name to show on screen
    description: str
    example: str


class DifficultyInfo(BaseModel):
    name: QuestionDifficulty
    description: str


class QuestionOptionsResponse(BaseModel):
    categories: list[CategoryInfo]
    difficulties: list[DifficultyInfo]
    count_min: int
    count_max: int
    count_default: int
