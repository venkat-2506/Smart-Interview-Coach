"""Resume upload API router."""

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.backend.auth.dependencies import get_current_user
from app.backend.database.session import get_db
from app.backend.models.resume import Resume
from app.backend.models.user import User
from app.backend.services.resume_service import upload_resume

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/upload", status_code=201)
def upload(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Upload a PDF resume for the authenticated user.

    Validates content type (PDF only) and size (max 5 MB).
    Stores the file in data/uploads/ and records metadata in the database.
    """
    record: Resume = upload_resume(file, current_user, db)
    return {
        "message": "Resume uploaded successfully.",
        "resume_id": record.id,
        "original_filename": record.original_filename,
        "stored_filename": record.stored_filename,
        "upload_time": record.upload_time.isoformat(),
    }
