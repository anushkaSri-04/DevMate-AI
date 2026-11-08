
"""Index a GitHub repository into DevMate AI's vector database."""

from typing import Any

from devmate.services.source_code import (
    retrieve_python_source_files,
)
from devmate.services.code_chunker import (
    chunk_repository,
)
from devmate.services.embedding_service import (
    EmbeddingService,
)
from devmate.services.vector_store import (
    VectorStore,
)
from devmate.services.repository_cache import repository_cache


class RepositoryIndexer:
    """Retrieve, process, embed and index repository source code."""

    def __init__(
        self,
        persist_directory: str = "data/chroma",
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.embedding_service = EmbeddingService(
            model_name=embedding_model
        )

        self.vector_store = VectorStore(
            persist_directory=persist_directory
        )

    def index_repository(
        self,
        github: Any,
        owner: str,
        repo: str,
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Index Python source files from an existing GitHub snapshot."""

        repository = snapshot.get("repository")

        if not repository:
            raise ValueError(
                "Snapshot does not contain a repository identifier."
            )
        # Remove previously cached repository data.
        repository_cache.invalidate_repository(repository)
        print(f"\n===== INDEXING {repository} =====")

        # 1. Retrieve Python source files.
        print("\n[1/4] Retrieving Python source files...")

        retrieval_result = retrieve_python_source_files(
            github=github,
            owner=owner,
            repo=repo,
            snapshot=snapshot,
        )

        source_files = retrieval_result["files"]
        # Cache source files for subsequent repository Q&A.
        repository_cache.set_source_files(
            repository=repository,
            source_files=source_files,
        )

        if not source_files:
            return {
                "repository": repository,
                "status": "no_files",
                "total_python_files_found": (
                    retrieval_result["total_python_files_found"]
                ),
                "total_files_analyzed": 0,
                "total_chunks": 0,
                "total_chunks_stored": 0,
                "failed_files": retrieval_result["failed_files"],
                "truncated": retrieval_result["truncated"],
            }

        print(
            "Files retrieved:",
            len(source_files),
        )

        # 2. Extract meaningful code chunks.
        print("\n[2/4] Extracting code chunks...")

        chunks = chunk_repository(
            source_files=source_files,
            repository=repository,
        )

        print("Code chunks extracted:", len(chunks))

        if not chunks:
            return {
                "repository": repository,
                "status": "no_chunks",
                "total_python_files_found": (
                    retrieval_result["total_python_files_found"]
                ),
                "total_files_analyzed": len(source_files),
                "total_chunks": 0,
                "total_chunks_stored": 0,
                "failed_files": retrieval_result["failed_files"],
                "truncated": retrieval_result["truncated"],
            }

        # 3. Generate embeddings.
        print("\n[3/4] Generating embeddings...")

        embedded_chunks = self.embedding_service.embed_chunks(
            chunks
        )

        print(
            "Embeddings generated:",
            len(embedded_chunks),
        )

        # 4. Store embeddings in ChromaDB.
        print("\n[4/4] Storing vectors in ChromaDB...")

        stored_count = self.vector_store.add_chunks(
            repository=repository,
            chunks=embedded_chunks,
        )

        total_stored = self.vector_store.count_chunks(
            repository
        )

        result = {
            "repository": repository,
            "status": "success",
            "total_python_files_found": (
                retrieval_result["total_python_files_found"]
            ),
            "total_files_analyzed": len(source_files),
            "total_chunks": len(chunks),
            "total_chunks_stored": stored_count,
            "total_chunks_in_database": total_stored,
            "failed_files": retrieval_result["failed_files"],
            "truncated": retrieval_result["truncated"],
        }

        print("\n===== INDEXING COMPLETED =====")
        print("Repository:", repository)
        print("Files analyzed:", len(source_files))
        print("Chunks extracted:", len(chunks))
        print("Chunks stored:", stored_count)
        print("Total chunks in database:", total_stored)
        print("Failed files:", len(retrieval_result["failed_files"]))

        return result
