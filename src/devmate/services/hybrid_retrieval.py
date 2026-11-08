"""Hybrid lexical and semantic retrieval for DevMate AI."""

from typing import Any

from devmate.services.context_retrieval import (
    build_context_package,
    extract_source_context,
)
from devmate.services.embedding_service import EmbeddingService
from devmate.services.vector_store import VectorStore


class HybridRetriever:
    """Combine AST-based lexical retrieval with vector similarity search."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.embedding_service = (
            embedding_service or EmbeddingService()
        )
        self.vector_store = vector_store or VectorStore()

    @staticmethod
    def _context_key(context: dict) -> tuple:
        """Identify the same source-code section across retrieval methods."""

        return (
            context.get("file"),
            context.get("start_line"),
            context.get("end_line"),
        )

    @staticmethod
    def _reciprocal_rank(rank: int, k: int = 60) -> float:
        """Calculate a Reciprocal Rank Fusion contribution."""

        return 1.0 / (k + rank)

    def retrieve(
        self,
        analysis: dict[str, Any],
        source_files: list[dict[str, Any]],
        query: str,
        repository: str | None = None,
        max_contexts: int = 10,
        semantic_top_k: int = 10,
        rrf_k: int = 60,
    ) -> dict[str, Any]:
        """
        Retrieve and rank code using lexical and semantic search.

        Lexical retrieval:
            AST symbols, references, imports, files and keywords.

        Semantic retrieval:
            Embeddings and ChromaDB similarity search.

        Final ranking:
            Reciprocal Rank Fusion (RRF).
        """

        if not query or not query.strip():
            return {
                "repository": repository,
                "query": query,
                "total_contexts": 0,
                "lexical_results": 0,
                "semantic_results": 0,
                "contexts": [],
                "related_files": [],
                "insufficient_context": True,
            }

        repository = repository or analysis.get("repository")

        if not repository:
            raise ValueError(
                "Repository identifier is required for hybrid retrieval."
            )

        # ----------------------------------------------------
        # 1. Existing lexical and contextual retrieval
        # ----------------------------------------------------

        lexical_package = build_context_package(
            analysis=analysis,
            source_files=source_files,
            query=query,
            max_contexts=max_contexts * 2,
        )

        lexical_contexts = lexical_package["code_context"]

        # ----------------------------------------------------
        # 2. Semantic retrieval through ChromaDB
        # ----------------------------------------------------

        query_embedding = self.embedding_service.embed_query(query)

        semantic_results = self.vector_store.search(
            repository=repository,
            query_embedding=query_embedding,
            top_k=semantic_top_k,
        )

        source_contexts = {}

        # ----------------------------------------------------
        # 3. Prepare lexical results
        # ----------------------------------------------------

        for context in lexical_contexts:
            key = self._context_key(context)

            if not all(key):
                continue

            if key not in source_contexts:
                source_contexts[key] = {
                    **context,
                    "retrieval_sources": ["lexical"],
                    "rrf_score": 0.0,
                }

        # ----------------------------------------------------
        # 4. Prepare semantic results
        # ----------------------------------------------------

        semantic_contexts = []

        for result in semantic_results:
            metadata = result.get("metadata", {})

            file_path = metadata.get("file")
            start_line = metadata.get("start_line")
            end_line = metadata.get("end_line")

            if (
                not file_path
                or start_line is None
                or end_line is None
            ):
                continue

            source = extract_source_context(
                source_files=source_files,
                file_path=file_path,
                start_line=int(start_line),
                end_line=int(end_line),
                padding=2,
            )

            if source is None:
                continue

            context = {
                **source,
                "type": "semantic_match",
                "symbol": metadata.get("symbol"),
                "semantic_similarity": result.get("similarity"),
                "vector_distance": result.get("distance"),
                "vector_chunk_id": result.get("id"),
                "retrieval_sources": ["semantic"],
                "rrf_score": 0.0,
            }

            semantic_contexts.append(context)

        # ----------------------------------------------------
        # 5. Apply Reciprocal Rank Fusion
        # ----------------------------------------------------

        for rank, context in enumerate(
            lexical_contexts,
            start=1,
        ):
            key = self._context_key(context)

            if key not in source_contexts:
                continue

            source_contexts[key]["rrf_score"] += (
                self._reciprocal_rank(rank, rrf_k)
            )

        for rank, context in enumerate(
            semantic_contexts,
            start=1,
        ):
            key = self._context_key(context)

            if key not in source_contexts:
                source_contexts[key] = context

            else:
                existing = source_contexts[key]

                if "semantic" not in existing["retrieval_sources"]:
                    existing["retrieval_sources"].append("semantic")

                existing["semantic_similarity"] = (
                    context["semantic_similarity"]
                )
                existing["vector_distance"] = (
                    context["vector_distance"]
                )
                existing["vector_chunk_id"] = (
                    context["vector_chunk_id"]
                )

            source_contexts[key]["rrf_score"] += (
                self._reciprocal_rank(rank, rrf_k)
            )

        # ----------------------------------------------------
        # 6. Sort combined results
        # ----------------------------------------------------

        combined_contexts = list(source_contexts.values())

        combined_contexts.sort(
            key=lambda item: (
                -item["rrf_score"],
                item["file"],
                item["start_line"],
            )
        )

        selected_contexts = combined_contexts[:max_contexts]

        # ----------------------------------------------------
        # 7. Return hybrid retrieval package
        # ----------------------------------------------------

        return {
            "repository": repository,
            "query": query,
            "total_contexts": len(selected_contexts),
            "lexical_results": len(lexical_contexts),
            "semantic_results": len(semantic_contexts),
            "total_candidates": len(combined_contexts),
            "contexts": selected_contexts,
            "related_files": lexical_package["related_files"],
            "insufficient_context": len(selected_contexts) == 0,
            "retrieval_method": "hybrid_rrf",
        }