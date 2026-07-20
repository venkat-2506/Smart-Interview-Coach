"""Service layer for managing interviews."""

import json
import uuid
from loguru import logger
from sqlalchemy.orm import Session

from app.backend.core.exceptions import AppException
from app.backend.models.resume import Resume
from app.backend.interview.models import InterviewSession, InterviewMessage
from app.backend.interview.schemas import (
    InterviewStartRequest,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
)
from app.backend.interview.graph import interview_graph


def start_interview(user_id: int, request: InterviewStartRequest, db: Session) -> InterviewSession:
    """Start a new interview session.

    Retrieves user's resume, executes LangGraph Planner and Question Generator,
    persists the session and first question, and returns the session details.
    """
    # 1. Fetch user's latest processed resume
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == user_id, Resume.is_processed)
        .order_by(Resume.upload_time.desc())
        .first()
    )
    if not resume:
        raise AppException(
            "No processed resume found. Please upload and analyze a resume first.",
            status_code=404,
        )

    # 2. Setup session variables
    session_id = str(uuid.uuid4())
    logger.info(f"Starting new interview session {session_id} for user {user_id}")

    # 3. Create initial state for LangGraph execution
    initial_state = {
        "resume_context": resume.extracted_text or "",
        "selected_role": request.role,
        "interview_mode": request.mode,
        "interview_plan": {},
        "remaining_plan": [],
        "covered_topics": [],
        "interview_history": [],
        "question_number": 1,
        "current_stage": "resume_discussion",
        "current_topic": "general introduction",
        "current_difficulty": "medium",
        "current_question": "",
        "new_question_metadata": None,
    }

    # 4. Invoke LangGraph (runs Planner and Question Generator to form the plan and 1st question)
    try:
        final_state = interview_graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"LangGraph execution failed during start_interview: {e}")
        raise AppException("Failed to initialize interview plan.", status_code=500)

    # 5. Extract results from LangGraph
    plan_dict = final_state.get("interview_plan", {})
    first_question = final_state.get("current_question", "")
    metadata = final_state.get("new_question_metadata") or {}

    stage = metadata.get("stage", "resume_discussion")
    topic = metadata.get("topic", "general introduction")
    difficulty = metadata.get("difficulty", "medium")

    # 6. Create database session record
    session_record = InterviewSession(
        session_id=session_id,
        user_id=user_id,
        resume_id=resume.id,
        selected_role=request.role,
        interview_mode=request.mode,
        interview_status="active",
        current_question_number=1,
        current_stage=stage,
        current_topic=topic,
        current_difficulty=difficulty,
        interview_plan=json.dumps(plan_dict),
        covered_topics=json.dumps([topic]),
        camera_enabled=request.camera_enabled,
        microphone_enabled=request.microphone_enabled,
        cv_analysis_status="active" if request.camera_enabled else "inactive",
        speech_analysis_status="active" if request.microphone_enabled else "inactive",
    )
    db.add(session_record)

    # 7. Create database message record for the first question
    first_msg = InterviewMessage(
        session_id=session_id,
        sender="AI",
        message=first_question,
        question_number=1,
        question_type=metadata.get("question_type", "resume"),
        topic=topic,
        difficulty=difficulty,
        stage=stage,
    )
    db.add(first_msg)

    db.commit()
    db.refresh(session_record)

    logger.info(f"Interview session {session_id} successfully created and first question saved.")
    return session_record


def submit_answer(
    session_id: str, user_id: int, request: AnswerSubmitRequest, db: Session
) -> AnswerSubmitResponse:
    """Submit a response, advance the plan, invoke LangGraph, and return the next question."""
    # 1. Fetch active session and verify user ownership
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.session_id == session_id)
        .first()
    )
    if not session:
        raise AppException("Interview session not found.", status_code=404)
    if session.user_id != user_id:
        raise AppException("Access denied.", status_code=403)

    if session.interview_status == "completed":
        return AnswerSubmitResponse(
            session_id=session_id,
            completed=True,
            message="Interview is already completed.",
        )

    # 2. Persist user's response in DB
    user_msg = InterviewMessage(
        session_id=session_id,
        sender="User",
        message=request.answer,
        question_number=session.current_question_number,
        stage=session.current_stage,
        topic=session.current_topic,
        difficulty=session.current_difficulty,
    )
    db.add(user_msg)
    db.commit()

    # 3. Read dynamic plan & history
    plan_dict = json.loads(session.interview_plan or "{}")
    covered_topics = json.loads(session.covered_topics or "[]")
    plan_list = plan_dict.get("plan", [])

    # Count AI questions asked in the current stage
    ai_questions_in_stage = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.session_id == session_id,
            InterviewMessage.sender == "AI",
            InterviewMessage.stage == session.current_stage,
        )
        .count()
    )

    # Determine current stage parameters
    current_stage_idx = 0
    for idx, step in enumerate(plan_list):
        if step.get("stage") == session.current_stage:
            current_stage_idx = idx
            break

    current_step = plan_list[current_stage_idx] if plan_list else {}
    target_count = current_step.get("question_count", 1)

    # 4. Advance plan if question count target for the current stage has been reached
    next_stage_idx = current_stage_idx
    if ai_questions_in_stage >= target_count:
        next_stage_idx += 1

    # Check if we have completed the entire plan
    if next_stage_idx >= len(plan_list):
        session.interview_status = "completed"
        db.commit()
        logger.info(f"Interview session {session_id} completed successfully.")
        return AnswerSubmitResponse(
            session_id=session_id,
            completed=True,
            message="Thank you! The interview has been completed.",
        )

    # Fetch next stage details
    next_step = plan_list[next_stage_idx]
    next_stage = next_step.get("stage")
    next_difficulty = next_step.get("difficulty", "medium")

    # Select next topic from the step's topic list that is not yet covered
    next_topic = next_step.get("topics", ["general"])[0]
    for topic_item in next_step.get("topics", []):
        if topic_item not in covered_topics:
            next_topic = topic_item
            break

    # 5. Fetch past messages to populate LangGraph history context
    messages = (
        db.query(InterviewMessage)
        .filter(InterviewMessage.session_id == session_id)
        .order_by(InterviewMessage.created_at.asc())
        .all()
    )
    history_list = [
        {"sender": m.sender, "message": m.message} for m in messages
    ]

    # Fetch resume text for prompt context
    resume = db.get(Resume, session.resume_id)
    resume_text = resume.extracted_text if resume else ""

    # 6. Setup State for LangGraph
    next_question_num = session.current_question_number + 1
    state = {
        "resume_context": resume_text,
        "selected_role": session.selected_role,
        "interview_mode": session.interview_mode,
        "interview_plan": plan_dict,
        "remaining_plan": plan_list[next_stage_idx:],
        "covered_topics": covered_topics,
        "interview_history": history_list,
        "question_number": next_question_num,
        "current_stage": next_stage,
        "current_topic": next_topic,
        "current_difficulty": next_difficulty,
        "current_question": "",
        "new_question_metadata": None,
    }

    # 7. Invoke LangGraph (skips Planner node and executes Question Generator)
    try:
        final_state = interview_graph.invoke(state)
    except Exception as e:
        logger.error(f"LangGraph execution failed during submit_answer: {e}")
        raise AppException("Failed to generate the next question.", status_code=500)

    # 8. Extract next question and update DB
    next_question = final_state.get("current_question", "")
    metadata = final_state.get("new_question_metadata") or {}

    stage_result = metadata.get("stage", next_stage)
    topic_result = metadata.get("topic", next_topic)
    difficulty_result = metadata.get("difficulty", next_difficulty)

    if topic_result not in covered_topics:
        covered_topics.append(topic_result)

    session.current_question_number = next_question_num
    session.current_stage = stage_result
    session.current_topic = topic_result
    session.current_difficulty = difficulty_result
    session.covered_topics = json.dumps(covered_topics)

    # 9. Save new AI question in message log
    ai_msg = InterviewMessage(
        session_id=session_id,
        sender="AI",
        message=next_question,
        question_number=next_question_num,
        question_type=metadata.get("question_type", "technical"),
        topic=topic_result,
        difficulty=difficulty_result,
        stage=stage_result,
    )
    db.add(ai_msg)
    db.commit()

    logger.info(f"Generated Q#{next_question_num} for session {session_id}")
    return AnswerSubmitResponse(
        session_id=session_id,
        completed=False,
        next_question_number=next_question_num,
        next_question=next_question,
        next_stage=stage_result,
        next_topic=topic_result,
        next_difficulty=difficulty_result,
        message="Next question generated.",
    )


def get_session(session_id: str, user_id: int, db: Session) -> InterviewSession:
    """Retrieve session details and verify ownership."""
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.session_id == session_id)
        .first()
    )
    if not session:
        raise AppException("Interview session not found.", status_code=404)
    if session.user_id != user_id:
        raise AppException("Access denied.", status_code=403)
    return session


def end_interview(session_id: str, user_id: int, db: Session) -> InterviewSession:
    """Conclude an interview session early."""
    session = get_session(session_id, user_id, db)
    session.interview_status = "completed"
    db.commit()
    db.refresh(session)
    logger.info(f"Interview session {session_id} manually ended.")
    return session
