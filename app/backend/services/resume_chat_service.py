"""Resume Knowledge Assistant Service.

Orchestrates the full conversational RAG pipeline:
    1. Guardrail check — reject off-topic questions.
    2. Retrieve relevant resume chunks via FAISS.
    3. Build a contextual prompt with history.
    4. Call the LLM and return a natural language answer.
"""

from loguru import logger
from sqlalchemy.orm import Session

from app.ai.llm.client import get_llm_response
from app.ai.prompts.resume_prompts import build_chat_prompt, build_guardrail_prompt
from app.ai.rag.retriever import ResumeRetriever
from app.backend.core.exceptions import AppException
from app.backend.models.resume import Resume
from app.backend.schemas.resume_chat import ChatMessage

OFF_TOPIC_REPLY = (
    "I can help only with questions related to your uploaded resume, "
    "interview preparation, technical concepts, and career guidance."
)


def answer_resume_question(
    resume_id: int,
    question: str,
    history: list[ChatMessage],
    top_k: int,
    db: Session,
) -> dict:
    """Run the full conversational RAG pipeline for a user question.

    Steps:
        1. Validate the resume exists and is indexed.
        2. Run the guardrail to reject off-topic questions.
        3. Retrieve relevant resume chunks via FAISS.
        4. Build the chat prompt with context and history.
        5. Call the LLM and return the natural language answer.

    Args:
        resume_id: The database ID of the user's resume.
        question: The user's current question.
        history: Previous conversation messages (most recent last).
        top_k: Number of FAISS chunks to retrieve.
        db: Active SQLAlchemy session.

    Returns:
        A dict with keys: "answer" (str), "is_off_topic" (bool).

    Raises:
        AppException 404: If the resume does not exist or is not indexed.
    """
    # Step 1: Validate resume state
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise AppException(f"Resume with id={resume_id} not found.", status_code=404)
    if not resume.is_indexed:
        raise AppException(
            "Resume has not been indexed yet. Please re-upload your resume.",
            status_code=422,
        )

    logger.info(f"Chat request for resume_id={resume_id}, question='{question[:60]}'")

    # Step 2: Guardrail — classify the question topic
    guardrail_prompt = build_guardrail_prompt(question)
    try:
        classification = get_llm_response(guardrail_prompt).strip().upper()
    except Exception as e:
        logger.warning(f"Guardrail LLM call failed, defaulting to RELEVANT: {e}")
        classification = "RELEVANT"

    if "OFF_TOPIC" in classification:
        logger.info(f"Guardrail rejected question for resume_id={resume_id}")
        return {"answer": OFF_TOPIC_REPLY, "is_off_topic": True}

    # Step 3: Retrieve relevant chunks
    retriever = ResumeRetriever()
    try:
        chunks = retriever.retrieve(resume_id, question, top_k)
    except Exception as e:
        logger.error(f"FAISS retrieval failed for resume_id={resume_id}: {e}")
        raise AppException("Failed to search resume. Please try again.", status_code=500)

    chunk_texts = [c["chunk_text"] for c in chunks]
    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    # Step 4: Build prompt and call LLM
    prompt = build_chat_prompt(
        question=question,
        context_chunks=chunk_texts,
        history=history_dicts,
    )

    try:
        answer = get_llm_response(prompt).strip()
    except Exception as e:
        logger.error(f"LLM call failed for resume_id={resume_id}: {e}")
        raise AppException(
            "The AI assistant is temporarily unavailable. Please try again.",
            status_code=503,
        )

    logger.info(f"Chat response generated for resume_id={resume_id}")
    return {"answer": answer, "is_off_topic": False}
