"""Resume API router.

Contains all resume-related endpoints:
    - POST /resume/upload         — Upload a PDF resume
    - POST /resume/{id}/analyze   — Trigger AI analysis pipeline
    - GET  /resume/{id}           — Get resume metadata
    - GET  /resume/{id}/analysis  — Get structured AI analysis
    - GET  /resume/{id}/skills    — Get extracted skills
    - GET  /resume/{id}/role      — Get detected role
"""

import json

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.backend.auth.dependencies import get_current_user
from app.backend.core.exceptions import AppException
from app.backend.database.session import get_db
from app.backend.models.resume import Resume
from app.backend.models.user import User
from app.backend.schemas.resume import (
    ResumeAnalysisResponse,
    ResumeMetadataResponse,
    ResumeRoleResponse,
    ResumeSkillsResponse,
)
from app.backend.services.resume_intelligence_service import process_resume
from app.backend.services.resume_service import upload_resume

router = APIRouter(prefix="/resume", tags=["Resume"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_resume_for_user(resume_id: int, current_user: User, db: Session) -> Resume:
    """Fetch a resume by ID and verify it belongs to the current user.

    Raises:
        AppException 404: If the resume does not exist.
        AppException 403: If the resume belongs to a different user.
    """
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise AppException(f"Resume with id={resume_id} not found.", status_code=404)
    if resume.user_id != current_user.id:
        raise AppException("Access denied.", status_code=403)
    return resume


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload", status_code=201)
def upload(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Upload a PDF resume for the authenticated user.

    Validates content type (PDF only) and size (max 5 MB).
    Stores the file in data/uploads/ and records metadata in the database.
    Automatically triggers AI analysis after upload.
    """
    # Step 1: Save the file and create the database record
    record: Resume = upload_resume(file, current_user, db)

    # Step 2: Automatically run the AI intelligence pipeline
    processed_record: Resume = process_resume(record.id, db)

    return {
        "message": "Resume uploaded and analyzed successfully.",
        "resume_id": processed_record.id,
        "original_filename": processed_record.original_filename,
        "stored_filename": processed_record.stored_filename,
        "upload_time": processed_record.upload_time.isoformat(),
        "is_processed": processed_record.is_processed,
    }


@router.get("/{resume_id}", response_model=ResumeMetadataResponse)
def get_resume_metadata(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resume:
    """Return metadata for a specific resume."""
    return _get_resume_for_user(resume_id, current_user, db)


@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisResponse)
def get_resume_analysis(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeAnalysisResponse:
    """Return the structured AI analysis of a resume.

    The analysis includes name, email, phone, education, experience,
    projects, certifications, skills, and technologies extracted by Gemini.
    """
    resume = _get_resume_for_user(resume_id, current_user, db)

    if not resume.resume_analysis:
        return ResumeAnalysisResponse(
            resume_id=resume_id,
            message="This resume has not been analyzed yet.",
        )

    analysis_dict = json.loads(resume.resume_analysis)
    return ResumeAnalysisResponse(
        resume_id=resume_id,
        analysis=analysis_dict,
        message="Analysis complete.",
    )


@router.get("/{resume_id}/skills", response_model=ResumeSkillsResponse)
def get_resume_skills(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeSkillsResponse:
    """Return extracted and categorized skills from a resume."""
    resume = _get_resume_for_user(resume_id, current_user, db)

    if not resume.extracted_skills:
        return ResumeSkillsResponse(
            resume_id=resume_id,
            message="Skills have not been extracted yet.",
        )

    skills_dict = json.loads(resume.extracted_skills)
    return ResumeSkillsResponse(
        resume_id=resume_id,
        skills=skills_dict,
        message="Skills extracted.",
    )


@router.get("/{resume_id}/role", response_model=ResumeRoleResponse)
def get_resume_role(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeRoleResponse:
    """Return the detected primary and alternative job roles for a resume."""
    resume = _get_resume_for_user(resume_id, current_user, db)

    if not resume.detected_role:
        return ResumeRoleResponse(
            resume_id=resume_id,
            message="Role has not been detected yet.",
        )

    role_dict = json.loads(resume.detected_role)
    return ResumeRoleResponse(
        resume_id=resume_id,
        role=role_dict,
        message="Role detected.",
    )
