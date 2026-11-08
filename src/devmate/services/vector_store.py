
"""Persistent ChromaDB vector storage for DevMate AI."""

import hashlib
import re
from pathlib import Path
from typing import Any

import chromadb


class VectorStore:
    """Store and retrieve repository code embeddings using ChromaDB."""

    def __init__(
        self,
        persist_directory: str = "data/chroma",
    ) -> None:
        self.persist_directory = str(Path(persist_directory))

        Path(self.persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

    @staticmethod
    def _get_collection_name(repository: str) -> str:
        """Generate a valid, repository-specific collection name."""

        if not repository or not repository.strip():
            raise ValueError("Repository name cannot be empty.")

        normalized = repository.strip().lower()

        safe_name = re.sub(
            r"[^a-z0-9_-]+",
            "_",
            normalized,
        ).strip("_-")

        # Hash prevents collisions between similar repository names.
        repository_hash = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()[:10]

        collection_name = f"devmate_{safe_name[:40]}_{repository_hash}"

        return collection_name

    def get_collection(self, repository: str):
        """Get or create a collection for a repository."""

        collection_name = self._get_collection_name(repository)

        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": f"Code embeddings for {repository}",
                "hnsw:space": "cosine",
            },
        )

    @staticmethod
    def _validate_chunk(chunk: dict[str, Any]) -> None:
        """Validate a chunk before storing it."""

        required_fields = [
            "id",
            "text",
            "embedding",
            "metadata",
        ]

        for field in required_fields:
            if field not in chunk:
                raise ValueError(
                    f"Chunk is missing required field: {field}"
                )

        if not chunk["id"]:
            raise ValueError("Chunk ID cannot be empty.")

        if not chunk["text"]:
            raise ValueError("Chunk text cannot be empty.")

        if not chunk["embedding"]:
            raise ValueError("Chunk embedding cannot be empty.")

        if not isinstance(chunk["metadata"], dict):
            raise ValueError("Chunk metadata must be a dictionary.")

        if any(
            not isinstance(value, (str, int, float, bool))
            for value in chunk["metadata"].values()
        ):
            raise ValueError(
                "ChromaDB metadata values must be scalar values."
            )

    def add_chunks(
        self,
        repository: str,
        chunks: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """Insert or update code chunks and their embeddings."""

        if not chunks:
            return 0

        if batch_size < 1:
            raise ValueError("batch_size must be at least 1.")

        for chunk in chunks:
            self._validate_chunk(chunk)

            chunk_repository = (
                chunk["metadata"].get("repository", "")
            )

            if (
                chunk_repository
                and chunk_repository != repository
            ):
                raise ValueError(
                    "Chunk repository does not match target collection."
                )

        collection = self.get_collection(repository)

        embedding_dimensions = {
            len(chunk["embedding"])
            for chunk in chunks
        }

        if len(embedding_dimensions) != 1:
            raise ValueError(
                "All embeddings must have the same dimensions."
            )

        # Remove duplicate IDs within the input batch.
        unique_chunks = {
            chunk["id"]: chunk
            for chunk in chunks
        }

        chunks_to_store = list(unique_chunks.values())

        for start in range(0, len(chunks_to_store), batch_size):
            batch = chunks_to_store[
                start:start + batch_size
            ]

            collection.upsert(
                ids=[
                    chunk["id"]
                    for chunk in batch
                ],
                documents=[
                    chunk["text"]
                    for chunk in batch
                ],
                embeddings=[
                    chunk["embedding"]
                    for chunk in batch
                ],
                metadatas=[
                    chunk["metadata"]
                    for chunk in batch
                ],
            )

        return len(chunks_to_store)

    def search(
        self,
        repository: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve semantically similar code chunks."""

        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        collection = self.get_collection(repository)

        if collection.count() == 0:
            return []

        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        matches = []

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for chunk_id, document, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):
            matches.append({
                "id": chunk_id,
                "text": document,
                "metadata": metadata,
                "distance": distance,
                "similarity": max(
                    0.0,
                    min(1.0, 1.0 - distance),
                ),
            })

        return matches

    def count_chunks(self, repository: str) -> int:
        """Return the number of stored chunks."""

        collection = self.get_collection(repository)

        return collection.count()

    def delete_repository(self, repository: str) -> None:
        """Delete all indexed chunks for a repository."""

        collection_name = self._get_collection_name(repository)

        self.client.delete_collection(
            name=collection_name
        )

    def list_repositories(self) -> list[str]:
        """List repository collections stored in ChromaDB."""

        return [
            collection.name
            for collection in self.client.list_collections()
            if collection.name.startswith("devmate_")
        ]
