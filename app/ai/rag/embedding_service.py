"""Embedding Service Module.

Provides a provider-independent interface for generating vector embeddings.
Encapsulates Sentence Transformers loading and execution.
"""

from typing import Optional
from loguru import logger
from sentence_transformers import SentenceTransformer

from config import get_settings


class EmbeddingService:
    """Service class for generating embeddings using Sentence Transformers."""

    # Class-level model cache to act as a singleton across instances
    _model_instance: Optional[SentenceTransformer] = None

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the embedding service.

        Args:
            model_name: Optional name of the model to load. If omitted, loads from settings.
        """
        self.settings = get_settings()
        self.model_name = model_name or self.settings.embedding_model_name

    @classmethod
    def _get_model(cls, model_name: str) -> SentenceTransformer:
        """Get or load the SentenceTransformer instance (thread-safe cache)."""
        if cls._model_instance is None:
            logger.info(f"Loading SentenceTransformer model: {model_name}...")
            try:
                cls._model_instance = SentenceTransformer(model_name)
                logger.info(f"SentenceTransformer model {model_name} loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model {model_name}: {e}")
                raise ValueError(f"Could not load embedding model: {e}") from e
        return cls._model_instance

    def embed_query(self, text: str) -> list[float]:
        """Generate an embedding for a single text query.

        Args:
            text: Query string.

        Returns:
            A list of floats representing the query vector.
        """
        model = self._get_model(self.model_name)
        try:
            vector = model.encode(text, convert_to_numpy=True).tolist()
            return vector
        except Exception as e:
            logger.error(f"Failed to generate embedding for query: {e}")
            raise ValueError(f"Embedding generation failed: {e}") from e

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of documents.

        Args:
            texts: List of document strings.

        Returns:
            A list of float lists representing document vectors.
        """
        if not texts:
            return []

        model = self._get_model(self.model_name)
        try:
            vectors = model.encode(texts, convert_to_numpy=True).tolist()
            return vectors
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise ValueError(f"Batch embedding generation failed: {e}") from e
