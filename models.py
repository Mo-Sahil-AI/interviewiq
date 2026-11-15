import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(
        default=False, server_default=text("false"), nullable=False
    )
    email_verification_token_hash = Column(String(64))
    email_verification_expires_at = Column(DateTime)
    password_reset_token_hash = Column(String(64))
    password_reset_expires_at = Column(DateTime)
    password_changed_at = Column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True,default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    version_no = Column(
        Integer,
        nullable=False
    )

    file_name = Column(
        String(255)
    )

    resume_text = Column(
        Text,
        nullable=False
    )

    resume_hash = Column(
        String(64)
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(UUID(as_uuid=True), primary_key=True,default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    version_no = Column(
        Integer,
        nullable=False
    )

    job_description = Column(
        Text,
        nullable=False
    )

    jd_hash = Column(
        String(64)
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


class ResumeAnalysis(Base):
    __tablename__ = "resume_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True,default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    analysis_version = Column(
        Integer,
        nullable=False
    )

    resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id"),
        nullable=False
    )

    jd_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id"),
        nullable=False
    )

    resume_version = Column(
        Integer,
        nullable=False
    )

    jd_version = Column(
        Integer,
        nullable=False
    )

    overview = Column(Text)

    match_analysis = Column(Text)

    irrelevant_content = Column(Text)

    missing_requirements = Column(Text)

    suggestions = Column(Text)

    others = Column(JSONB)

    analysis_hash = Column(
    String(64),
    nullable=False
)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True
    )

    current_resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id")
    )

    current_resume_version = Column(
        Integer
    )

    current_jd_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id")
    )

    current_jd_version = Column(
        Integer
    )

    current_analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resume_analysis.id")
    )

    current_analysis_version = Column(
        Integer
    )

    updated_at = Column(
        DateTime,
        server_default=func.now()
    )


class Question(Base):
    """Every interview question ever generated for a user.

    The generator reads this table so it never repeats itself, and the mock
    interviewer will read it later to pick what to ask.
    """

    __tablename__ = "questions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    # Which generation round (1, 2, 3 ...) and the order inside that round
    batch_no = Column(
        Integer,
        nullable=False
    )

    item_no = Column(
        Integer,
        nullable=False
    )

    # What the questions were based on
    resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id"),
        nullable=False
    )

    jd_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id"),
        nullable=False
    )

    resume_version = Column(
        Integer,
        nullable=False
    )

    jd_version = Column(
        Integer,
        nullable=False
    )

    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resume_analysis.id")
    )

    category = Column(
        String(20),
        nullable=False
    )

    difficulty = Column(
        String(10),
        nullable=False
    )

    target_skill = Column(
        String(100)
    )

    question_text = Column(
        Text,
        nullable=False
    )

    # Fingerprint of the normalised text: the exact-repeat guard
    question_hash = Column(
        String(64),
        nullable=False
    )

    # What a strong answer would cover (list of short points)
    ideal_answer_points = Column(JSONB)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "question_hash",
            name="unique_user_question_hash"
        ),
        UniqueConstraint(
            "user_id", "batch_no", "item_no",
            name="unique_user_question_batch_item"
        ),
        CheckConstraint(
            "category IN ('technical', 'behavioral', 'situational', 'resume_based', 'hr')",
            name="questions_category_check"
        ),
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="questions_difficulty_check"
        ),
        Index(
            "idx_questions_user_batch",
            "user_id", "batch_no", "item_no"
        ),
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    resume_version = Column(Integer, nullable=False)
    jd_id = Column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False
    )
    jd_version = Column(Integer, nullable=False)
    interview_type = Column(String(20), nullable=False, default="mixed")
    duration_seconds = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="preparing")
    current_turn_no = Column(Integer, nullable=False, default=0)
    questions_asked = Column(Integer, nullable=False, default=0)
    overall_score = Column(Integer)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "interview_type IN ('technical', 'behavioral', 'mixed', 'resume_based')",
            name="interview_sessions_type_check",
        ),
        CheckConstraint(
            "status IN ('preparing', 'active', 'completed', 'interrupted', 'failed')",
            name="interview_sessions_status_check",
        ),
        CheckConstraint(
            "duration_seconds BETWEEN 60 AND 3600",
            name="interview_sessions_duration_check",
        ),
        CheckConstraint("current_turn_no >= 0", name="interview_sessions_turn_check"),
        CheckConstraint(
            "questions_asked >= 0", name="interview_sessions_questions_check"
        ),
        Index("idx_interview_sessions_user_created", "user_id", "created_at"),
        Index("idx_interview_sessions_user_status", "user_id", "status"),
        Index(
            "uq_active_interview_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status IN ('preparing', 'active')"),
        ),
    )


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False
    )
    turn_no = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_category = Column(String(20), nullable=False)
    difficulty = Column(String(10), nullable=False)
    user_transcript = Column(Text)
    answer_started_at = Column(DateTime)
    answer_ended_at = Column(DateTime)
    answer_duration_ms = Column(Integer)
    answer_score = Column(Integer)
    answer_feedback = Column(Text)
    is_completed = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("session_id", "turn_no", name="unique_interview_turn"),
        CheckConstraint(
            "question_category IN ('technical', 'behavioral', 'situational', 'resume_based', 'hr')",
            name="interview_turn_category_check",
        ),
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="interview_turn_difficulty_check",
        ),
        Index("idx_interview_turns_session_turn", "session_id", "turn_no"),
    )


class InterviewSummary(Base):
    __tablename__ = "interview_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=False,
        unique=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    overall_score = Column(Integer)
    strong_areas = Column(JSONB)
    weak_areas = Column(JSONB)
    skills_to_learn = Column(JSONB)
    job_requirements_missing = Column(JSONB)
    technical_feedback = Column(JSONB)
    behavioral_feedback = Column(JSONB)
    communication_feedback = Column(JSONB)
    recommendations = Column(JSONB)
    summary_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_interview_summaries_user_created", "user_id", "created_at"),
    )


class VoiceAnalysis(Base):
    __tablename__ = "voice_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False
    )
    turn_id = Column(
        UUID(as_uuid=True), ForeignKey("interview_turns.id"), nullable=False, unique=True
    )
    transcript = Column(Text)
    language = Column(String(16))
    speaking_rate_wpm = Column(Integer)
    pause_count = Column(Integer)
    long_pause_count = Column(Integer)
    filler_word_count = Column(Integer)
    repeated_word_count = Column(Integer)
    grammar_score = Column(Integer)
    fluency_score = Column(Integer)
    clarity_score = Column(Integer)
    pronunciation_score = Column(Integer)
    confidence_score = Column(Integer)
    pace_score = Column(Integer)
    grammar_issues = Column(JSONB)
    filler_words = Column(JSONB)
    pronunciation_notes = Column(JSONB)
    voice_feedback = Column(Text)
    analysis_status = Column(
        String(20), nullable=False, default="completed", server_default=text("'completed'")
    )
    analysis_provider = Column(String(40))
    analysis_error = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_voice_analyses_session_created", "session_id", "created_at"),
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="assistant_messages_role_check",
        ),
        Index("idx_assistant_messages_user_created", "user_id", "created_at"),
    )
