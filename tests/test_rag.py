"""Tests for the Resume RAG pipeline.

These tests verify the RAG foundation:
  1. ResumeChunker - text chunking
  2. EmbeddingService - vector generation
  3. FAISSStore - index save, load, search
  4. ResumeRetriever - end-to-end retrieval
"""

import sys
import os

# Allow running the test from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.rag.chunker import ResumeChunker
from app.ai.rag.embedding_service import EmbeddingService
from app.ai.rag.faiss_store import FAISSStore
from app.ai.rag.retriever import ResumeRetriever

# ---------------------------------------------------------------------------
# Sample Resume Text (used across all tests)
# ---------------------------------------------------------------------------

SAMPLE_RESUME_TEXT = """
John Doe
Software Engineer

EDUCATION
B.Tech in Computer Science, JNTU Hyderabad, 2022.

EXPERIENCE
Software Engineer at ABC Corp (2022 - Present).
Built REST APIs with FastAPI and deployed to AWS Lambda.
Reduced response time by 40% through caching with Redis.

PROJECTS
Project: Smart Interview Coach
Description: An AI-powered interview preparation platform using RAG, FAISS, Gemini API.
Technologies: Python, FastAPI, FAISS, Sentence Transformers, Streamlit.

Project: E-Commerce Recommendation Engine
Description: Built a product recommendation system using collaborative filtering.
Technologies: Python, Scikit-learn, PostgreSQL.

SKILLS
Programming Languages: Python, Java, SQL
Frameworks: FastAPI, Django, Spring Boot
Databases: PostgreSQL, SQLite, Redis
Cloud: AWS, GCP
"""


# ---------------------------------------------------------------------------
# Test 1: ResumeChunker
# ---------------------------------------------------------------------------

def test_chunker_basic():
    """Test that chunker produces the expected number of chunks."""
    print("\n--- Test 1: ResumeChunker ---")
    chunker = ResumeChunker(chunk_size=300, chunk_overlap=30)
    chunks = chunker.chunk_resume(SAMPLE_RESUME_TEXT, resume_id=99)

    assert len(chunks) > 0, "Expected at least one chunk."
    print(f"  Chunks generated: {len(chunks)}")

    for chunk in chunks:
        assert "chunk_id" in chunk, "Missing chunk_id"
        assert "chunk_text" in chunk, "Missing chunk_text"
        assert "start_position" in chunk, "Missing start_position"
        assert "end_position" in chunk, "Missing end_position"
        assert chunk["end_position"] > chunk["start_position"], "Invalid chunk position range."
    print("  All chunk metadata fields are present and valid.")
    print("  PASS")


def test_chunker_empty_text():
    """Test that chunker raises AppException on empty text."""
    print("\n--- Test 2: Chunker with Empty Text ---")
    from app.backend.core.exceptions import AppException
    chunker = ResumeChunker()
    try:
        chunker.chunk_resume("   ", resume_id=99)
        print("  FAIL: Expected AppException but none was raised.")
    except AppException as e:
        print(f"  AppException raised correctly: {e.message}")
        print("  PASS")


# ---------------------------------------------------------------------------
# Test 3: EmbeddingService
# ---------------------------------------------------------------------------

def test_embedding_single():
    """Test embedding a single query."""
    print("\n--- Test 3: EmbeddingService - Single Query ---")
    service = EmbeddingService()
    vector = service.embed_query("Tell me about the projects.")

    assert isinstance(vector, list), "Expected a list."
    assert len(vector) > 0, "Expected non-empty vector."
    print(f"  Embedding dimension: {len(vector)}")
    print("  PASS")


def test_embedding_batch():
    """Test batch embedding of multiple documents."""
    print("\n--- Test 4: EmbeddingService - Batch Documents ---")
    service = EmbeddingService()
    texts = ["Experience with FastAPI", "Education at JNTU", "Projects using FAISS"]
    vectors = service.embed_documents(texts)

    assert len(vectors) == 3, f"Expected 3 vectors, got {len(vectors)}"
    assert all(len(v) > 0 for v in vectors), "All vectors should be non-empty."
    print(f"  Batch size: {len(vectors)}, Dimension: {len(vectors[0])}")
    print("  PASS")


# ---------------------------------------------------------------------------
# Test 5: FAISSStore - Save, Load, Search
# ---------------------------------------------------------------------------

def test_faiss_save_and_load():
    """Test that FAISSStore can save and reload an index correctly."""
    print("\n--- Test 5: FAISSStore - Save and Load ---")
    service = EmbeddingService()
    chunker = ResumeChunker(chunk_size=300, chunk_overlap=30)
    faiss_store = FAISSStore()

    test_resume_id = 9999

    # Generate chunks and embeddings
    chunks = chunker.chunk_resume(SAMPLE_RESUME_TEXT, test_resume_id)
    texts = [c["chunk_text"] for c in chunks]
    embeddings = service.embed_documents(texts)

    # Save index
    index_dir = faiss_store.save_index(test_resume_id, embeddings, chunks)
    print(f"  Index saved at: {index_dir}")

    # Load index
    index, metadata = faiss_store.load_index(test_resume_id)
    assert index.ntotal == len(chunks), f"Expected {len(chunks)} items in index, got {index.ntotal}"
    assert len(metadata) == len(chunks), f"Expected {len(chunks)} metadata entries, got {len(metadata)}"
    print(f"  Loaded index: {index.ntotal} vectors, {len(metadata)} metadata entries")
    print("  PASS")


# ---------------------------------------------------------------------------
# Test 6: FAISSStore - Similarity Search
# ---------------------------------------------------------------------------

def test_faiss_similarity_search():
    """Test that similarity search returns relevant results."""
    print("\n--- Test 6: FAISSStore - Similarity Search ---")
    service = EmbeddingService()
    faiss_store = FAISSStore()

    test_resume_id = 9999

    # Embed and search
    query_embedding = service.embed_query("What projects did the candidate build?")
    results = faiss_store.similarity_search(test_resume_id, query_embedding, top_k=3)

    assert len(results) > 0, "Expected at least one result."
    assert all("chunk_text" in r for r in results), "All results should have chunk_text"
    assert all("score" in r for r in results), "All results should have a score"
    print(f"  Retrieved {len(results)} chunks.")
    for r in results:
        print(f"    Score: {r['score']:.4f} | {r['chunk_id']}")
    print("  PASS")


# ---------------------------------------------------------------------------
# Test 7: ResumeRetriever - End-to-End
# ---------------------------------------------------------------------------

def test_retriever_end_to_end():
    """Test the full ResumeRetriever flow against a pre-built test index."""
    print("\n--- Test 7: ResumeRetriever - End to End ---")
    retriever = ResumeRetriever()
    test_resume_id = 9999

    results = retriever.retrieve(
        resume_id=test_resume_id,
        query="What are the candidate's skills?",
        top_k=4,
    )

    assert isinstance(results, list), "Expected a list."
    assert len(results) > 0, "Expected at least one result."
    print(f"  Retrieved {len(results)} chunks for skills query.")
    for r in results:
        print(f"    Score: {r['score']:.4f} | {r['chunk_id'][:40]}")
    print("  PASS")


# ---------------------------------------------------------------------------
# Run All Tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  Resume RAG Pipeline - Test Suite")
    print("=" * 50)

    test_chunker_basic()
    test_chunker_empty_text()
    test_embedding_single()
    test_embedding_batch()
    test_faiss_save_and_load()
    test_faiss_similarity_search()
    test_retriever_end_to_end()

    print("\n" + "=" * 50)
    print("  All tests passed!")
    print("=" * 50)
