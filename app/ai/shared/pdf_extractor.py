"""PDF text extraction utility.

Responsibility: Take a file path and return the extracted plain text.
Nothing else. This is a reusable utility that future AI modules can import.
"""

import re
from pathlib import Path

from loguru import logger
from pypdf import PdfReader

from app.backend.core.exceptions import AppException


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from a PDF file and return it as a clean string.

    This function reads every page of the PDF, joins the text together,
    and then passes it to the text cleaner before returning.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        The full extracted text as a single string.

    Raises:
        AppException 422: If the PDF cannot be read or yields no text.
    """
    logger.info(f"Starting PDF text extraction: {file_path.name}")

    if not file_path.exists():
        raise AppException(f"PDF file not found: {file_path}", status_code=404)

    try:
        reader = PdfReader(str(file_path))
    except Exception as e:
        logger.error(f"Failed to open PDF '{file_path.name}': {e}")
        raise AppException(
            "The PDF file could not be read. It may be corrupted.",
            status_code=422,
        ) from e

    page_texts = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text()
            if page_text:
                page_texts.append(page_text)
        except Exception as e:
            # Log the warning but continue processing remaining pages
            logger.warning(f"Could not extract text from page {page_number}: {e}")

    if not page_texts:
        raise AppException(
            "No text could be extracted from this PDF. "
            "It may be a scanned image PDF.",
            status_code=422,
        )

    full_text = "\n".join(page_texts)
    logger.info(
        f"PDF extraction complete: {file_path.name} "
        f"({len(reader.pages)} pages, {len(full_text)} characters)"
    )

    return full_text
