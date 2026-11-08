
from unittest.mock import MagicMock

from devmate.services.repository_qa import RepositoryQA
from devmate.services.conversation_context import ConversationContext


def test_followup_question_uses_conversation_history():
    retriever = MagicMock()
    retriever.retrieve.return_value = {
        "contexts": [{
            "file": "tools/github_tools.py",
            "symbol": "list_issues",
            "start_line": 10,
            "end_line": 25,
            "snippet": "def list_issues():\n    pass",
            "retrieval_sources": ["lexical", "semantic"],
        }],
        "lexical_results": 5,
        "semantic_results": 5,
        "total_candidates": 8,
        "retrieval_method": "hybrid_rrf",
    }

    client = MagicMock()
    client.models.generate_content.return_value.text = (
        "The function is called by the issue retrieval tool."
    )

    conversation = ConversationContext()

    qa = RepositoryQA(
        retriever=retriever,
        client=client,
        conversation_context=conversation,
    )

    analysis = {"repository": "anushkaSri-04/DevMate-AI"}

    # First question
    qa.answer(
        analysis=analysis,
        source_files=[],
        question="Explain list_issues.",
        session_id="session_1",
    )

    # Follow-up question
    result = qa.answer(
        analysis=analysis,
        source_files=[],
        question="Where is this function called?",
        session_id="session_1",
    )

    # Verify previous conversation was used for retrieval.
    second_call = retriever.retrieve.call_args_list[1]
    retrieval_query = second_call.kwargs["query"]

    assert "list_issues" in retrieval_query
    assert "Previous conversation" in retrieval_query

    # Verify previous conversation reached Gemini.
    second_prompt = client.models.generate_content.call_args_list[1].kwargs["contents"]

    assert "list_issues" in second_prompt
    assert "Previous conversation" in second_prompt

    assert result["status"] == "success"


def test_different_sessions_have_separate_history():
    retriever = MagicMock()
    retriever.retrieve.return_value = {
        "contexts": [{
            "file": "tools/github_tools.py",
            "symbol": "list_issues",
            "start_line": 10,
            "end_line": 25,
            "snippet": "def list_issues():\n    pass",
            "retrieval_sources": ["lexical"],
        }],
        "lexical_results": 1,
        "semantic_results": 1,
        "total_candidates": 1,
        "retrieval_method": "hybrid_rrf",
    }

    client = MagicMock()
    client.models.generate_content.return_value.text = "Answer."

    conversation = ConversationContext()

    qa = RepositoryQA(
        retriever=retriever,
        client=client,
        conversation_context=conversation,
    )

    analysis = {"repository": "anushkaSri-04/DevMate-AI"}

    qa.answer(
        analysis, [], "Explain list_issues.",
        session_id="session_1",
    )

    qa.answer(
        analysis, [], "Explain GitHubClient.",
        session_id="session_2",
    )

    assert len(conversation.get_history("session_1")) == 2
    assert len(conversation.get_history("session_2")) == 2

    assert "list_issues" in conversation.get_history("session_1")[0]["content"]
    assert "GitHubClient" in conversation.get_history("session_2")[0]["content"]
