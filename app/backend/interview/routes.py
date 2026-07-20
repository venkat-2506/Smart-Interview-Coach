"""FastAPI router mapping interview endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.auth.dependencies import get_current_user
from app.backend.database.session import get_db
from app.backend.models.user import User
from app.backend.interview import controller
from app.backend.interview.schemas import (
    InterviewStartRequest,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    InterviewSessionResponse,
)

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/start", response_model=InterviewSessionResponse, status_code=201)
def start(
    request: InterviewStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewSessionResponse:
    """Create a new interview session and execute the Planner & Question Generator."""
    return controller.start_interview_session(current_user.id, request, db)


@router.get("/{session_id}", response_model=InterviewSessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewSessionResponse:
    """Retrieve details, stages, and current status of an interview session."""
    return controller.get_interview_session(session_id, current_user.id, db)


@router.post("/{session_id}/answer", response_model=AnswerSubmitResponse)
def submit_answer(
    session_id: str,
    request: AnswerSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnswerSubmitResponse:
    """Submit the user response to the current question and generate the next question."""
    return controller.submit_answer(session_id, current_user.id, request, db)


@router.post("/{session_id}/end", response_model=InterviewSessionResponse)
def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewSessionResponse:
    """End the active interview session early."""
    return controller.end_interview_session(session_id, current_user.id, db)
