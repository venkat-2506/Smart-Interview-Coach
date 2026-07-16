"""FAISS Vector Store wrapper.

Handles building, saving, loading, and searching a local FAISS index,
with structured JSON sidecar metadata.
"""

import json
import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from loguru import logger

from app.backend.core.exceptions import AppException
from config import get_settings


class FAISSStore:
    """Helper class to manage FAISS index files and sidecar metadata on disk."""

    def __init__(self):
        """Initialize the store with configuration settings."""
        self.settings = get_settings()
        self.indexes_dir = Path(self.settings.rag_index_dir)

    def _get_resume_dir(self, resume_id: int) -> Path:
        """Get the specific directory for a resume's index files.

        Example: data/indexes/resume_1/
        """
        return self.indexes_dir / f"resume_{resume_id}"

    def save_index(self, resume_id: int, embeddings: list[list[float]], metadata: list[dict]) -> str:
        """Create and serialize a FAISS index and its metadata for a resume.

        Args:
            resume_id: The database ID of the resume.
            embeddings: List of embedding vectors for the chunks.
            metadata: List of chunk metadata dictionaries.

        Returns:
            The string path to the created directory containing the index files.

        Raises:
            AppException 500: If vector store serialization fails.
        """
        if not embeddings:
            logger.error("Cannot create FAISS index with empty embeddings.")
            raise AppException("No embeddings provided to build FAISS index.", status_code=500)

        try:
            # 1. Prepare target directory
            resume_dir = self._get_resume_dir(resume_id)
            resume_dir.mkdir(parents=True, exist_ok=True)

            # 2. Build FAISS index
            dimension = len(embeddings[0])
            embeddings_np = np.array(embeddings).astype("float32")

            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_np)

            # 3. Write index binary
            index_path = resume_dir / "index.faiss"
            faiss.write_index(index, str(index_path))

            # 4. Write sidecar metadata
            metadata_path = resume_dir / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)

            logger.info(f"Successfully saved FAISS index to {resume_dir} (dimension={dimension}, size={index.ntotal})")
            return str(resume_dir)

        except Exception as e:
            logger.error(f"Failed to save FAISS index for resume_id={resume_id}: {e}")
            raise AppException(f"Failed to serialize FAISS vector index: {e}", status_code=500) from e

    def load_index(self, resume_id: int) -> tuple[faiss.Index, list[dict]]:
        """Load the FAISS index and metadata for a given resume from disk.

        Args:
            resume_id: The database ID of the resume.

        Returns:
            A tuple of (faiss_index, list_of_chunk_metadata).

        Raises:
            AppException 404: If the index files do not exist.
            AppException 422: If the index files are corrupted or cannot be read.
        """
        resume_dir = self._get_resume_dir(resume_id)
        index_path = resume_dir / "index.faiss"
        metadata_path = resume_dir / "metadata.json"

        if not index_path.exists() or not metadata_path.exists():
            logger.error(f"FAISS index files not found in {resume_dir}")
            raise AppException("Resume RAG index not found. Please index the resume first.", status_code=404)

        # 1. Load FAISS index
        try:
            index = faiss.read_index(str(index_path))
        except Exception as e:
            logger.error(f"Failed to read FAISS index binary at {index_path}: {e}")
            raise AppException("FAISS index binary is corrupted or unreadable.", status_code=422) from e

        # 2. Load sidecar metadata
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata JSON at {metadata_path}: {e}")
            raise AppException("RAG metadata file is corrupted or unreadable.", status_code=422) from e

        # 3. Consistency check
        if index.ntotal != len(metadata):
            logger.error(f"Mismatch: FAISS index has {index.ntotal} items, metadata has {len(metadata)}")
            raise AppException("Vector index and metadata sizes do not match.", status_code=422)

        return index, metadata

    def similarity_search(self, resume_id: int, query_embedding: list[float], top_k: int = 4) -> list[dict]:
        """Perform similarity search on the local index.

        Args:
            resume_id: The database ID of the resume to search.
            query_embedding: The embedded vector of the query.
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            A list of dictionary chunks with relevance score (distance):
            [
                {
                    "chunk_id": "...",
                    "chunk_text": "...",
                    "start_position": ...,
                    "end_position": ...,
                    "score": float(L2 distance)
                }
            ]
        """
        index, metadata = self.load_index(resume_id)

        # Cap top_k to the number of items in the index
        actual_k = min(top_k, index.ntotal)
        if actual_k <= 0:
            return []

        # Perform search
        query_np = np.array([query_embedding]).astype("float32")
        distances, indices = index.search(query_np, actual_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            chunk = metadata[idx].copy()
            # FAISS IndexFlatL2 returns squared L2 distance. Lower is closer.
            chunk["score"] = float(dist)
            results.append(chunk)

        return results
