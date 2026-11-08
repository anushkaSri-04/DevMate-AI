
from devmate.services.embedding_service import EmbeddingService


def test_embedding_service():

    service = EmbeddingService()

    text = "Retrieve GitHub issues using authenticated API requests."

    embedding = service.embed_text(text)

    print("\n===== EMBEDDING TEST =====")
    print("Embedding dimensions:", len(embedding))
    print("First 5 values:", embedding[:5])

    assert len(embedding) == 384
    assert all(isinstance(value, float) for value in embedding)

    query_embedding = service.embed_query(
        "How does GitHub authentication work?"
    )

    assert len(query_embedding) == 384

    print("\nEmbedding generation test passed!")


if __name__ == "__main__":
    test_embedding_service()
