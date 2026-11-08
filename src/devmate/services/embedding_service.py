
"""Generate semantic embeddings for DevMate AI code chunks."""

from typing import Any

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Generate embeddings for code and natural-language queries."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""

        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")

        vector = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return vector.tolist()

    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts."""

        if not texts:
            return []

        if any(not text or not text.strip() for text in texts):
            raise ValueError("Input contains empty text.")

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return vectors.tolist()

    def embed_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate embeddings while preserving chunk metadata."""

        if not chunks:
            return []

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embed_texts(texts)

        return [
            {
                **chunk,
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

    def embed_query(self, query: str) -> list[float]:
        """Generate an embedding for a developer's question."""

        return self.embed_text(query)
