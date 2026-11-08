
from unittest.mock import Mock, patch

from devmate.services.hybrid_retrieval import HybridRetriever


def test_hybrid_retrieval():
    repository = "test-owner/test-repo"

    source_files = [
        {
            "file": "src/github_client.py",
            "content": (
                "def get_issues():\n"
                "    return ['issue-1']\n"
            ),
        }
    ]

    lexical_context = {
        "file": "src/github_client.py",
        "start_line": 1,
        "end_line": 2,
        "symbol": "get_issues",
        "type": "function",
        "code": (
            "def get_issues():\n"
            "    return ['issue-1']"
        ),
    }

    semantic_match = {
        "id": "chunk-1",
        "metadata": {
            "file": "src/github_client.py",
            "start_line": 1,
            "end_line": 2,
            "symbol": "get_issues",
        },
        "similarity": 0.95,
        "distance": 0.05,
    }

    embedding_service = Mock()
    embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]

    vector_store = Mock()
    vector_store.search.return_value = [semantic_match]

    retriever = HybridRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    with (
        patch(
            "devmate.services.hybrid_retrieval.build_context_package"
        ) as mock_lexical,
        patch(
            "devmate.services.hybrid_retrieval.extract_source_context"
        ) as mock_source,
    ):
        mock_lexical.return_value = {
            "code_context": [lexical_context],
            "related_files": [],
        }

        mock_source.return_value = lexical_context.copy()

        result = retriever.retrieve(
            analysis={"repository": repository},
            source_files=source_files,
            query="How are GitHub issues retrieved?",
            repository=repository,
            max_contexts=5,
            semantic_top_k=10,
        )

    assert result["total_contexts"] > 0
    assert result["lexical_results"] == 1
    assert result["semantic_results"] == 1
    assert result["total_candidates"] == 1
    assert result["retrieval_method"] == "hybrid_rrf"
    assert result["insufficient_context"] is False

    context = result["contexts"][0]

    assert set(context["retrieval_sources"]) == {
        "lexical",
        "semantic",
    }

    assert context["semantic_similarity"] == 0.95

    expected_rrf_score = (1 / 61) + (1 / 61)

    assert abs(
        context["rrf_score"] - expected_rrf_score
    ) < 1e-9

    embedding_service.embed_query.assert_called_once_with(
        "How are GitHub issues retrieved?"
    )

    vector_store.search.assert_called_once_with(
        repository=repository,
        query_embedding=[0.1, 0.2, 0.3],
        top_k=10,
    )
