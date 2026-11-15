import uuid
from datetime import datetime
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password must contain a non-whitespace character")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def password_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password must contain a non-whitespace character")
        return value


class PasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password must contain a non-whitespace character")
        return value


class ChangePasswordRequest(PasswordRequest):
    current_password: str = Field(min_length=1, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class TokenRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)


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


class AssistantMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must contain a non-whitespace character")
        return value


class AssistantMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class AssistantConversationResponse(BaseModel):
    messages: list[AssistantMessageOut]


InterviewType = Literal["technical", "behavioral", "mixed", "resume_based"]
InterviewStatus = Literal[
    "preparing", "active", "completed", "interrupted", "failed"
]


class CreateInterviewRequest(BaseModel):
    duration_seconds: int = Field(
        900, ge=60, le=3600,
        description="Interview duration in seconds. The browser accepts 1-60 minutes and converts to seconds.",
    )
    interview_type: InterviewType = "mixed"


class InterviewSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    resume_version: int
    jd_id: uuid.UUID
    jd_version: int
    interview_type: InterviewType
    duration_seconds: int
    status: InterviewStatus
    current_turn_no: int
    questions_asked: int
    overall_score: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime


class InterviewSessionListResponse(BaseModel):
    total: int
    items: list[InterviewSessionOut]


class InterviewSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    overall_score: int | None = None
    strong_areas: list[str] | None = None
    weak_areas: list[str] | None = None
    skills_to_learn: list[str] | None = None
    job_requirements_missing: list[str] | None = None
    technical_feedback: list[str] | None = None
    behavioral_feedback: list[str] | None = None
    communication_feedback: list[str] | None = None
    recommendations: list[str] | None = None
    summary_text: str | None = None
    created_at: datetime


class VoiceAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    turn_id: uuid.UUID
    transcript: str | None = None
    speaking_rate_wpm: int | None = None
    pause_count: int | None = None
    long_pause_count: int | None = None
    filler_word_count: int | None = None
    repeated_word_count: int | None = None
    grammar_score: int | None = None
    fluency_score: int | None = None
    clarity_score: int | None = None
    pronunciation_score: int | None = None
    confidence_score: int | None = None
    pace_score: int | None = None
    grammar_issues: list[str] | None = None
    filler_words: list[str] | None = None
    pronunciation_notes: list[str] | None = None
    voice_feedback: str | None = None
    analysis_status: str
    analysis_provider: str | None = None
    analysis_error: str | None = None
    created_at: datetime


class InterviewTurnReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    turn_no: int
    question_text: str
    question_category: str
    difficulty: str
    user_transcript: str | None = None
    answer_duration_ms: int | None = None
    answer_score: int | None = None
    answer_feedback: str | None = None
    is_completed: bool
    voice: VoiceAnalysisOut | None = None


class InterviewReviewResponse(BaseModel):
    session: InterviewSessionOut
    summary: InterviewSummaryOut | None = None
    turns: list[InterviewTurnReviewOut]
