"""Resume ORM model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.database.session import Base


class Resume(Base):
    """Stores metadata and AI analysis results for uploaded resume files.

    Columns added in Resume Intelligence phase:
        - extracted_text:  Raw text extracted from the PDF.
        - resume_analysis: JSON string from LLM structured analysis.
        - detected_role:   JSON string from LLM role detection.
        - extracted_skills:JSON string from LLM skill extraction.
        - is_processed:    True once the full AI pipeline has completed.
    """

    __tablename__ = "resumes"

    # --- Core Upload Fields ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    upload_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- AI Intelligence Fields (nullable until pipeline runs) ---
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_role: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- RAG Fields ---
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vector_index_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="resumes")
