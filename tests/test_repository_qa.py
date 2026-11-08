from unittest.mock import MagicMock

from devmate.services.repository_qa import RepositoryQA


def test_repository_qa_success():

    retriever = MagicMock()

    retriever.retrieve.return_value = {
        "contexts": [
            {
                "file": "tools/github_tools.py",
                "symbol": "list_issues",
                "start_line": 10,
                "end_line": 25,
                "snippet": "10: def list_issues():\n11: ...",
                "retrieval_sources": ["lexical", "semantic"],
            }
        ],
        "lexical_results": 5,
        "semantic_results": 5,
        "total_candidates": 8,
        "retrieval_method": "hybrid_rrf",
        "related_files": [],
    }

    client = MagicMock()
    client.models.generate_content.return_value.text = (
        "The list_issues function retrieves issues from GitHub."
    )

    qa = RepositoryQA(
        retriever=retriever,
        client=client,
    )

    result = qa.answer(
        analysis={"repository": "anushkaSri-04/DevMate-AI"},
        source_files=[],
        question="How are GitHub issues retrieved?",
    )

    assert result["status"] == "success"
    assert "list_issues" in result["answer"]
    assert len(result["evidence"]) == 1

    client.models.generate_content.assert_called_once()


def test_repository_qa_insufficient_context():

    retriever = MagicMock()

    retriever.retrieve.return_value = {
        "contexts": [],
        "lexical_results": 0,
        "semantic_results": 0,
        "total_candidates": 0,
        "related_files": [],
    }

    client = MagicMock()

    qa = RepositoryQA(
        retriever=retriever,
        client=client,
    )

    result = qa.answer(
        analysis={"repository": "anushkaSri-04/DevMate-AI"},
        source_files=[],
        question="Explain an unavailable feature.",
    )

    assert result["status"] == "insufficient_context"
    assert result["evidence"] == []

    client.models.generate_content.assert_not_called()