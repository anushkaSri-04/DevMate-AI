
from devmate.services.code_chunker import chunk_python_file
from devmate.services.embedding_service import EmbeddingService
from devmate.services.vector_store import VectorStore


def test_vector_store():

    repository = "devmate-test/vector-store"

    sample_code = """
def authenticate(token):
    return token is not None


def list_issues(owner, repo):
    return f"Fetching issues for {owner}/{repo}"


class GitHubClient:
    def get(self, endpoint):
        return endpoint
"""

    print("\n===== STEP 1: CODE CHUNKING =====")

    chunks = chunk_python_file(
        file_path="tools/github_tools.py",
        content=sample_code,
        repository=repository,
    )

    print("Chunks extracted:", len(chunks))

    assert len(chunks) >= 3

    print("\n===== STEP 2: GENERATING EMBEDDINGS =====")

    embedding_service = EmbeddingService()

    embedded_chunks = embedding_service.embed_chunks(
        chunks
    )

    print("Embeddings generated:", len(embedded_chunks))
    print(
        "Embedding dimensions:",
        len(embedded_chunks[0]["embedding"]),
    )

    assert len(embedded_chunks) == len(chunks)
    assert len(embedded_chunks[0]["embedding"]) == 384

    print("\n===== STEP 3: STORING IN CHROMADB =====")

    vector_store = VectorStore(
        persist_directory="data/chroma_test"
    )

    stored_count = vector_store.add_chunks(
        repository=repository,
        chunks=embedded_chunks,
    )

    print("Chunks stored:", stored_count)

    assert stored_count == len(chunks)

    total_count = vector_store.count_chunks(repository)

    print("Total stored chunks:", total_count)

    assert total_count == len(chunks)

    print("\n===== STEP 4: SEMANTIC SEARCH =====")

    query = "How does DevMate retrieve GitHub issues?"

    query_embedding = embedding_service.embed_query(query)

    results = vector_store.search(
        repository=repository,
        query_embedding=query_embedding,
        top_k=3,
    )

    print("Query:", query)
    print("\nRetrieved results:")

    for index, result in enumerate(results, start=1):
        print(f"\nResult {index}")
        print("Symbol:", result["metadata"]["symbol"])
        print("File:", result["metadata"]["file"])
        print("Type:", result["metadata"]["type"])
        print("Similarity:", round(result["similarity"], 4))
        print("Code:\n", result["text"])

    assert len(results) > 0

    print("\n===== STEP 5: REPOSITORY COLLECTION =====")

    repositories = vector_store.list_repositories()

    print("Collections:", repositories)

    assert vector_store._get_collection_name(
        repository
    ) in repositories

    print("\nVector store test passed!")


if __name__ == "__main__":
    test_vector_store()
