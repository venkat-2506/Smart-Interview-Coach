"""Resume Retriever.

Accepts a query, embeds it, and returns the most relevant
resume chunks using the FAISS vector store.
"""

from loguru import logger

from app.ai.rag.embedding_service import EmbeddingService
from app.ai.rag.faiss_store import FAISSStore


class ResumeRetriever:
    """Retrieves relevant resume chunks for a given query."""

    def __init__(self):
        """Initialize the retriever with embedding service and vector store."""
        self.embedding_service = EmbeddingService()
        self.faiss_store = FAISSStore()

    def retrieve(self, resume_id: int, query: str, top_k: int = 4) -> list[dict]:
        """Retrieve the top-k most relevant chunks for a query.

        Steps:
          1. Embed the user query into a vector.
          2. Search the FAISS index for the nearest chunks.
          3. Return the matching chunks with their metadata and scores.

        Args:
            resume_id: Database ID of the resume to search.
            query: The search query text.
            top_k: Number of results to return (default: 4).

        Returns:
            A list of chunk dictionaries sorted by relevance score (ascending L2 distance):
            [
                {
                    "chunk_id": "resume_1_chunk_5",
                    "chunk_text": "...",
                    "start_position": 1234,
                    "end_position": 1700,
                    "score": 0.15
                },
                ...
            ]
        """
        logger.info(f"Retrieving top_k={top_k} chunks for resume_id={resume_id} with query='{query[:60]}...'")

        # Step 1: Embed the query
        query_embedding = self.embedding_service.embed_query(query)

        # Step 2: Search FAISS
        results = self.faiss_store.similarity_search(resume_id, query_embedding, top_k)

        logger.info(f"Retrieved {len(results)} chunks for resume_id={resume_id}")
        return results
