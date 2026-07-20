"""Interview database models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.database.session import Base


class InterviewSession(Base):
    """Stores metadata and active states for an interview session."""

    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_role: Mapped[str] = mapped_column(String(255), nullable=False)
    interview_mode: Mapped[str] = mapped_column(String(100), nullable=False)  # "Mock Interview" or "Quick Assessment"
    interview_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # "active", "completed"

    # Current session state trackers
    current_question_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Dynamic plans and history represented as JSON string serialization
    interview_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    covered_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Camera/Mic config for future Computer Vision & Speech Analysis integration
    camera_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    microphone_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cv_analysis_status: Mapped[str] = mapped_column(String(50), default="inactive", nullable=False)
    speech_analysis_status: Mapped[str] = mapped_column(String(50), default="inactive", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="interview_sessions")
    resume = relationship("Resume", backref="interview_sessions")


class InterviewMessage(Base):
    """Stores individual message logs within an interview session."""

    __tablename__ = "interview_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("interview_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(50), nullable=False)  # "AI" or "User"
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Rich metadata for analytics, reporting, and adaptive memory
    question_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    question_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("InterviewSession", backref="messages")
