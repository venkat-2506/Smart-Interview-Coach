"""Pydantic schemas for the Resume RAG endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResumeIndexResponse(BaseModel):
    """Response returned after successfully indexing a resume."""

    resume_id: int
    chunk_count: int
    embedding_model: str
    vector_index_path: str
    indexed_at: datetime
    message: str


class ResumeStatusResponse(BaseModel):
    """Response returned for GET /resume/{id}/status."""

    resume_id: int
    is_indexed: bool
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    vector_index_path: Optional[str] = None
    indexed_at: Optional[datetime] = None
    message: str


class ResumeRetrieveRequest(BaseModel):
    """Request body for POST /resume/{id}/retrieve."""

    query: str = Field(..., min_length=1, description="The search query text.")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of chunks to return (1-20).")


class ChunkResponse(BaseModel):
    """Represents a single retrieved chunk."""

    chunk_id: str
    chunk_text: str
    start_position: int
    end_position: int
    score: float


class ResumeRetrieveResponse(BaseModel):
    """Response returned after retrieving chunks for a query."""

    resume_id: int
    query: str
    top_k: int
    chunks: list[ChunkResponse]
    message: str
