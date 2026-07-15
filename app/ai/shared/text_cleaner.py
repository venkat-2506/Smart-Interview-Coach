"""Text cleaning and normalization utility.

Responsibility: Take raw extracted text and return clean, normalized text.
This runs after PDF extraction and before any AI processing.
Keeping this separate makes it easy to improve text quality independently.
"""

import re


def clean_resume_text(raw_text: str) -> str:
    """Clean and normalize raw text extracted from a PDF.

    Steps performed:
        1. Replace Windows-style line endings with Unix-style.
        2. Remove non-printable characters (except newlines and tabs).
        3. Collapse multiple blank lines into a single blank line.
        4. Strip leading/trailing whitespace from each line.
        5. Strip the overall text.

    Args:
        raw_text: The raw string output from the PDF extractor.

    Returns:
        A normalized, clean string ready for AI processing.
    """
    # Step 1: Normalize line endings
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Step 2: Remove non-printable characters, but keep newlines (\n) and tabs (\t)
    text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)

    # Step 3: Strip leading and trailing whitespace from each individual line
    lines = [line.strip() for line in text.split("\n")]

    # Step 4: Collapse sequences of more than 2 consecutive blank lines into one
    cleaned_lines = []
    consecutive_blank_count = 0

    for line in lines:
        if line == "":
            consecutive_blank_count += 1
            if consecutive_blank_count <= 1:
                cleaned_lines.append(line)
        else:
            consecutive_blank_count = 0
            cleaned_lines.append(line)

    # Step 5: Join and strip the full text
    clean_text = "\n".join(cleaned_lines).strip()

    return clean_text
