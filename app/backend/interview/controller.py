"""Controller for managing Interview API request processing."""

from sqlalchemy.orm import Session

from app.backend.interview import service
from app.backend.interview.schemas import (
    InterviewStartRequest,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    InterviewSessionResponse,
)


def start_interview_session(user_id: int, request: InterviewStartRequest, db: Session) -> InterviewSessionResponse:
    """Create a new interview session and fetch the initial question."""
    session = service.start_interview(user_id, request, db)
    
    # Locate the first message to extract the initial question
    first_question = None
    if session.messages:
        first_question = session.messages[0].message
    elif len(session.messages) == 0:
        # Fallback to fetching from messages relation if lazy loaded
        db.refresh(session)
        if session.messages:
            first_question = session.messages[0].message
            
    return InterviewSessionResponse(
        session_id=session.session_id,
        selected_role=session.selected_role,
        interview_mode=session.interview_mode,
        interview_status=session.interview_status,
        current_question_number=session.current_question_number,
        current_question=first_question or "Could not fetch initial question.",
        current_stage=session.current_stage,
        current_topic=session.current_topic,
        current_difficulty=session.current_difficulty,
        camera_enabled=session.camera_enabled,
        microphone_enabled=session.microphone_enabled,
        cv_analysis_status=session.cv_analysis_status,
        speech_analysis_status=session.speech_analysis_status,
        created_at=session.created_at,
        messages=session.messages,
    )


def submit_answer(
    session_id: str, user_id: int, request: AnswerSubmitRequest, db: Session
) -> AnswerSubmitResponse:
    """Process user's response and fetch the next question from LangGraph."""
    return service.submit_answer(session_id, user_id, request, db)


def get_interview_session(session_id: str, user_id: int, db: Session) -> InterviewSessionResponse:
    """Retrieve session details and conversation logs."""
    session = service.get_session(session_id, user_id, db)
    
    # Identify the latest AI question text to display
    current_question = None
    ai_questions = [m for m in session.messages if m.sender == "AI"]
    if ai_questions:
        # Get message text for the highest/latest question number
        ai_questions_sorted = sorted(ai_questions, key=lambda x: x.created_at, reverse=True)
        current_question = ai_questions_sorted[0].message

    return InterviewSessionResponse(
        session_id=session.session_id,
        selected_role=session.selected_role,
        interview_mode=session.interview_mode,
        interview_status=session.interview_status,
        current_question_number=session.current_question_number,
        current_question=current_question,
        current_stage=session.current_stage,
        current_topic=session.current_topic,
        current_difficulty=session.current_difficulty,
        camera_enabled=session.camera_enabled,
        microphone_enabled=session.microphone_enabled,
        cv_analysis_status=session.cv_analysis_status,
        speech_analysis_status=session.speech_analysis_status,
        created_at=session.created_at,
        messages=session.messages,
    )


def end_interview_session(session_id: str, user_id: int, db: Session) -> InterviewSessionResponse:
    """Conclude an interview session early."""
    service.end_interview(session_id, user_id, db)
    return get_interview_session(session_id, user_id, db)
