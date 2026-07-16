"""Resume RAG Service.

Orchestrates the full Resume Indexing and Retrieval pipeline.
Business logic lives here. API routes just call into this service.

Pipeline:
    Resume text → Chunker → EmbeddingService → FAISSStore → Database
    Query       → EmbeddingService → FAISSStore → Chunks
"""

from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.orm import Session

from app.ai.rag.chunker import ResumeChunker
from app.ai.rag.embedding_service import EmbeddingService
from app.ai.rag.faiss_store import FAISSStore
from app.ai.rag.retriever import ResumeRetriever
from app.backend.core.exceptions import AppException
from app.backend.models.resume import Resume
from config import get_settings


def index_resume(resume_id: int, db: Session) -> dict:
    """Run the full RAG indexing pipeline for a resume.

    Steps:
        1. Load the resume record from the database.
        2. Validate that text has been extracted.
        3. Chunk the text using ResumeChunker.
        4. Generate embeddings using EmbeddingService.
        5. Save the FAISS index and metadata to disk.
        6. Update the resume record with index metadata.

    Args:
        resume_id: The database ID of the resume to index.
        db: The active SQLAlchemy database session.

    Returns:
        A dictionary with indexing results.

    Raises:
        AppException 404: If the resume does not exist.
        AppException 422: If the resume has no extracted text.
        AppException 500: If any step in the pipeline fails.
    """
    settings = get_settings()

    # Step 1: Load the resume record
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise AppException(f"Resume with id={resume_id} not found.", status_code=404)

    # Step 2: Validate that text extraction has been done
    if not resume.extracted_text or not resume.extracted_text.strip():
        raise AppException(
            "Resume has no extracted text. Please run AI analysis first via POST /resume/upload.",
            status_code=422,
        )

    logger.info(f"Starting RAG indexing pipeline for resume_id={resume_id}")

    # Step 3: Chunk the resume text
    chunker = ResumeChunker(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    chunks = chunker.chunk_resume(resume.extracted_text, resume_id)
    logger.info(f"Generated {len(chunks)} chunks for resume_id={resume_id}")

    # Step 4: Generate embeddings for all chunks
    embedding_service = EmbeddingService()
    chunk_texts = [chunk["chunk_text"] for chunk in chunks]

    logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
    embeddings = embedding_service.embed_documents(chunk_texts)
    logger.info(f"Embeddings generated for resume_id={resume_id}")

    # Step 5: Save FAISS index and metadata to disk
    faiss_store = FAISSStore()
    index_dir = faiss_store.save_index(resume_id, embeddings, chunks)
    logger.info(f"FAISS index saved at {index_dir} for resume_id={resume_id}")

    # Step 6: Update resume record with RAG metadata
    resume.is_indexed = True
    resume.vector_index_path = index_dir
    resume.chunk_count = len(chunks)
    resume.embedding_model = settings.embedding_model_name
    resume.indexed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(resume)

    logger.info(f"RAG indexing pipeline complete for resume_id={resume_id}")

    return {
        "resume_id": resume_id,
        "chunk_count": resume.chunk_count,
        "embedding_model": resume.embedding_model,
        "vector_index_path": resume.vector_index_path,
        "indexed_at": resume.indexed_at,
        "message": f"Resume indexed successfully with {resume.chunk_count} chunks.",
    }


def retrieve_resume_chunks(resume_id: int, query: str, top_k: int, db: Session) -> list[dict]:
    """Retrieve relevant resume chunks for a given query.

    Args:
        resume_id: The database ID of the resume to search.
        query: The user's search query text.
        top_k: Number of top results to return.
        db: The active SQLAlchemy database session.

    Returns:
        A list of chunk dictionaries with text, metadata, and relevance score.

    Raises:
        AppException 404: If the resume does not exist or has not been indexed.
    """
    # Verify resume exists and is indexed
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise AppException(f"Resume with id={resume_id} not found.", status_code=404)

    if not resume.is_indexed:
        raise AppException(
            "Resume has not been indexed yet. Please call POST /resume/{id}/index first.",
            status_code=404,
        )

    logger.info(f"Processing retrieval request for resume_id={resume_id}, query='{query[:60]}'")

    retriever = ResumeRetriever()
    results = retriever.retrieve(resume_id, query, top_k)

    return results
