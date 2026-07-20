"""Pydantic schemas for the Interview Engine endpoints."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    """Request body for POST /interview/start."""

    role: str = Field(..., description="Target job role selected by the user.")
    mode: str = Field(
        ...,
        description="Interview mode (e.g. 'Mock Interview' or 'Quick Assessment').",
    )
    camera_enabled: bool = Field(
        default=False, description="Whether camera is enabled for CV analysis."
    )
    microphone_enabled: bool = Field(
        default=False, description="Whether microphone is enabled for speech analysis."
    )


class InterviewMessageResponse(BaseModel):
    """Represents a single message logged within a session."""

    sender: str
    message: str
    question_number: Optional[int] = None
    question_type: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    stage: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewSessionResponse(BaseModel):
    """Full session details returned in GET /interview/{session_id}."""

    session_id: str
    selected_role: str
    interview_mode: str
    interview_status: str
    current_question_number: int
    current_question: Optional[str] = None
    current_stage: Optional[str] = None
    current_topic: Optional[str] = None
    current_difficulty: Optional[str] = None
    camera_enabled: bool
    microphone_enabled: bool
    cv_analysis_status: str
    speech_analysis_status: str
    created_at: datetime
    messages: List[InterviewMessageResponse] = []

    class Config:
        from_attributes = True


class AnswerSubmitRequest(BaseModel):
    """Request body for POST /interview/{session_id}/answer."""

    answer: str = Field(..., min_length=1, description="The user's response to the active question.")


class AnswerSubmitResponse(BaseModel):
    """Response returned after submitting an answer."""

    session_id: str
    completed: bool = Field(
        ..., description="True if the interview plan is finished and interview has concluded."
    )
    next_question_number: Optional[int] = None
    next_question: Optional[str] = None
    next_stage: Optional[str] = None
    next_topic: Optional[str] = None
    next_difficulty: Optional[str] = None
    message: str = Field(..., description="Status description.")
