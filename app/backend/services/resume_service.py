"""Resume upload business logic."""

import uuid
from pathlib import Path

from fastapi import UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.backend.core.exceptions import AppException
from app.backend.models.resume import Resume
from app.backend.models.user import User

UPLOAD_DIR = Path("data/uploads")
ALLOWED_CONTENT_TYPE = "application/pdf"
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def upload_resume(file: UploadFile, current_user: User, db: Session) -> Resume:
    """Validate, store, and record a resume PDF upload.

    Raises:
        AppException 415: if the file is not a PDF.
        AppException 413: if the file exceeds the maximum size.
    """
    _validate_file_type(file)
    content = _read_and_validate_size(file)

    stored_filename = _build_stored_filename(file.filename or "resume.pdf")
    _persist_file(content, stored_filename)

    record = Resume(
        user_id=current_user.id,
        original_filename=file.filename or "resume.pdf",
        stored_filename=stored_filename,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        f"Resume uploaded: user_id={current_user.id}, "
        f"file='{file.filename}', stored='{stored_filename}'"
    )
    return record


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_file_type(file: UploadFile) -> None:
    """Raise AppException if the uploaded file is not a PDF."""
    if file.content_type != ALLOWED_CONTENT_TYPE:
        raise AppException(
            "Only PDF files are accepted.",
            status_code=415,
        )


def _read_and_validate_size(file: UploadFile) -> bytes:
    """Read file bytes and raise AppException if size exceeds the limit."""
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise AppException(
            f"File exceeds the maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
            status_code=413,
        )
    return content


def _build_stored_filename(original: str) -> str:
    """Generate a UUID-prefixed filename to avoid collisions."""
    suffix = Path(original).suffix or ".pdf"
    return f"{uuid.uuid4().hex}{suffix}"


def _persist_file(content: bytes, stored_filename: str) -> None:
    """Write file bytes to the upload directory."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / stored_filename
    destination.write_bytes(content)
