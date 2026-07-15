"""Pydantic schemas for Resume API responses.

These schemas define the exact shape of data returned by resume endpoints.
Using Pydantic ensures the data is always validated and serialized correctly.
"""

import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResumeMetadataResponse(BaseModel):
    """Schema for resume metadata returned by GET /resume/{id}."""

    id: int
    user_id: int
    original_filename: str
    stored_filename: str
    upload_time: datetime
    is_processed: bool

    # Tell Pydantic to read values from SQLAlchemy model attributes
    model_config = {"from_attributes": True}


class ResumeAnalysisResponse(BaseModel):
    """Schema for AI analysis returned by GET /resume/{id}/analysis.

    The analysis field contains the full structured JSON from Gemini,
    returned as a plain Python dict for maximum flexibility.
    """

    resume_id: int
    analysis: Optional[dict] = None
    message: str = "Analysis not yet available."


class ResumeSkillsResponse(BaseModel):
    """Schema for extracted skills returned by GET /resume/{id}/skills."""

    resume_id: int
    skills: Optional[dict] = None
    message: str = "Skills not yet extracted."


class ResumeRoleResponse(BaseModel):
    """Schema for detected role returned by GET /resume/{id}/role."""

    resume_id: int
    role: Optional[dict] = None
    message: str = "Role not yet detected."
