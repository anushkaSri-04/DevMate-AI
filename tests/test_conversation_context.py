
import pytest

from devmate.services.conversation_context import ConversationContext


def test_add_and_get_history():
    context = ConversationContext()

    context.add_turn(
        "session_1",
        "How does list_issues work?",
        "It retrieves issues from GitHub.",
    )

    history = context.get_history("session_1")

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert "list_issues" in history[0]["content"]


def test_build_retrieval_query():
    context = ConversationContext()

    context.add_turn(
        "session_1",
        "Explain list_issues.",
        "It retrieves issues using the GitHub client.",
    )

    query = context.build_retrieval_query(
        "session_1",
        "Where is this function called?",
    )

    assert "Previous conversation" in query
    assert "list_issues" in query
    assert "Where is this function called?" in query


def test_separate_sessions():
    context = ConversationContext()

    context.add_turn("session_1", "Question 1", "Answer 1")
    context.add_turn("session_2", "Question 2", "Answer 2")

    assert len(context.get_history("session_1")) == 2
    assert len(context.get_history("session_2")) == 2


def test_history_limit():
    context = ConversationContext(max_turns=2)

    for i in range(3):
        context.add_turn(
            "session_1",
            f"Question {i}",
            f"Answer {i}",
        )

    history = context.get_history("session_1")

    assert len(history) == 4
    assert history[0]["content"] == "Question 1"


def test_clear_history():
    context = ConversationContext()

    context.add_turn("session_1", "Question", "Answer")
    context.clear_history("session_1")

    assert context.get_history("session_1") == []
    assert context.get_session_count() == 0


def test_empty_question_rejected():
    context = ConversationContext()

    with pytest.raises(ValueError):
        context.build_retrieval_query("session_1", "")


def test_empty_session_id_rejected():
    context = ConversationContext()

    with pytest.raises(ValueError):
        context.add_turn("", "Question", "Answer")
