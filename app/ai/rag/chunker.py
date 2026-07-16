"""Resume Chunking Module.

This module splits extracted resume text into semantically cohesive chunks
reusing LangChain's RecursiveCharacterTextSplitter.
"""

from loguru import logger
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.backend.core.exceptions import AppException


class ResumeChunker:
    """Service class for chunking text using RecursiveCharacterTextSplitter."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize the chunker with configuration settings.

        Args:
            chunk_size: Maximum character count per chunk.
            chunk_overlap: Overlap character count between consecutive chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_resume(self, text: str, resume_id: int) -> list[dict]:
        """Split the cleaned text of a resume into chunks.

        Calculates chunk offsets (start_position, end_position) and
        generates structured metadata for citation/highlights.

        Args:
            text: Cleaned full text of the resume.
            resume_id: The database ID of the resume.

        Returns:
            A list of dictionaries representing each chunk:
            [
                {
                    "chunk_id": "resume_1_chunk_0",
                    "chunk_text": "...",
                    "start_position": 0,
                    "end_position": 480
                },
                ...
            ]

        Raises:
            AppException 422: If resume text is empty or invalid.
        """
        if not text or not text.strip():
            logger.error(f"Cannot chunk empty resume text for resume_id={resume_id}")
            raise AppException("Resume text is empty and cannot be indexed.", status_code=422)

        raw_chunks = self.splitter.split_text(text)
        if not raw_chunks:
            logger.error(f"Text splitter returned no chunks for resume_id={resume_id}")
            raise AppException("No chunks generated from resume text.", status_code=422)

        logger.info(f"Splitting resume_id={resume_id} into {len(raw_chunks)} chunks (size={self.chunk_size}, overlap={self.chunk_overlap})")

        chunks = []
        search_start_idx = 0

        for idx, chunk_text in enumerate(raw_chunks):
            # Locate the chunk's position in the original text
            start_pos = text.find(chunk_text, search_start_idx)
            
            # Fallback if text finding fails or restarts
            if start_pos == -1:
                start_pos = text.find(chunk_text)
                if start_pos == -1:
                    start_pos = search_start_idx  # Default fallback

            end_pos = start_pos + len(chunk_text)
            
            # Advance search index to the start of this chunk to prevent matching older chunks
            search_start_idx = max(search_start_idx, start_pos + 1)

            chunks.append({
                "chunk_id": f"resume_{resume_id}_chunk_{idx}",
                "chunk_text": chunk_text,
                "start_position": start_pos,
                "end_position": end_pos
            })

        return chunks
