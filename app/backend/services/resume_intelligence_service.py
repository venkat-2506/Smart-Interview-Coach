"""Resume Intelligence Service.

This service is the main orchestrator for all resume AI processing.
It connects the PDF extractor, text cleaner, Gemini client, and
prompt templates together into a clean, step-by-step pipeline.

Every step is logged so failures are easy to trace.
"""

import json
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from app.ai.llm.gemini_client import get_gemini_json_response
from app.ai.prompts.resume_prompts import (
    build_resume_analysis_prompt,
    build_role_detection_prompt,
    build_skill_extraction_prompt,
)
from app.ai.shared.pdf_extractor import extract_text_from_pdf
from app.ai.shared.text_cleaner import clean_resume_text
from app.backend.core.exceptions import AppException
from app.backend.models.resume import Resume

UPLOAD_DIR = Path("data/uploads")


def process_resume(resume_id: int, db: Session) -> Resume:
    """Run the full Resume Intelligence pipeline for a given resume.

    This function:
        1. Loads the resume record from the database.
        2. Extracts text from the stored PDF file.
        3. Cleans and normalizes the text.
        4. Sends the text to Gemini for structured analysis.
        5. Detects the best-fit job role.
        6. Extracts and categorizes skills.
        7. Saves all results back to the database.
        8. Returns the updated Resume record.

    Args:
        resume_id: The database ID of the resume to process.
        db: The active SQLAlchemy database session.

    Returns:
        The updated Resume model instance with all AI fields populated.

    Raises:
        AppException 404: If no resume with the given ID exists.
        AppException 422: If text extraction fails.
        Exception: If any Gemini API call fails.
    """
    # Step 1: Load resume record from database
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise AppException(f"Resume with id={resume_id} not found.", status_code=404)

    logger.info(f"Starting resume intelligence pipeline for resume_id={resume_id}")

    # Step 2: Extract text from the PDF file on disk
    pdf_path = UPLOAD_DIR / resume.stored_filename
    raw_text = extract_text_from_pdf(pdf_path)

    # Step 3: Clean and normalize the extracted text
    clean_text = clean_resume_text(raw_text)

    # Step 4: Save the extracted text to the database
    resume.extracted_text = clean_text
    logger.info(f"Resume text extracted: {len(clean_text)} characters")

    # Step 5: Run Gemini analysis to extract structured information
    logger.info(f"Starting Gemini analysis for resume_id={resume_id}")
    analysis_prompt = build_resume_analysis_prompt(clean_text)
    analysis_result = get_gemini_json_response(analysis_prompt)
    resume.resume_analysis = json.dumps(analysis_result)
    logger.info(f"Resume analysis complete for resume_id={resume_id}")

    # Step 6: Detect the best-fit job role
    logger.info(f"Starting role detection for resume_id={resume_id}")
    role_prompt = build_role_detection_prompt(clean_text)
    role_result = get_gemini_json_response(role_prompt)
    resume.detected_role = json.dumps(role_result)
    logger.info(f"Role detection complete for resume_id={resume_id}: {role_result.get('primary_role')}")

    # Step 7: Extract and categorize skills
    logger.info(f"Starting skill extraction for resume_id={resume_id}")
    skill_prompt = build_skill_extraction_prompt(clean_text)
    skill_result = get_gemini_json_response(skill_prompt)
    resume.extracted_skills = json.dumps(skill_result)
    logger.info(f"Skill extraction complete for resume_id={resume_id}")

    # Step 8: Mark the resume as processed and save all changes
    resume.is_processed = True
    db.commit()
    db.refresh(resume)

    logger.info(f"Resume intelligence pipeline finished for resume_id={resume_id}")
    return resume
