from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey
)
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
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