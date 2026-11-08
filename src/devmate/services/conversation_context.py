
"""Maintains conversation history for repository Q&A."""

from collections import defaultdict
from typing import Any


class ConversationContext:
    """Manage recent conversation history for multiple sessions."""

    def __init__(self, max_turns: int = 5):
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1.")

        self.max_turns = max_turns
        self._sessions: dict[str, list[dict[str, str]]] = defaultdict(list)

    def add_turn(
        self,
        session_id: str,
        question: str,
        answer: str,
    ) -> None:
        """Store one user question and assistant answer."""

        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty.")

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not answer or not answer.strip():
            raise ValueError("Answer cannot be empty.")

        history = self._sessions[session_id]

        history.append({
            "role": "user",
            "content": question.strip(),
        })

        history.append({
            "role": "assistant",
            "content": answer.strip(),
        })

        # Keep only the most recent complete conversation turns.
        self._sessions[session_id] = history[-(self.max_turns * 2):]

    def get_history(
        self,
        session_id: str,
    ) -> list[dict[str, str]]:
        """Return conversation history for a session."""

        return list(self._sessions.get(session_id, []))

    def build_retrieval_query(
        self,
        session_id: str,
        question: str,
    ) -> str:
        """
        Enrich a follow-up question with recent conversation context.

        This is a lightweight context-enrichment strategy.
        It does not perform LLM-based query rewriting.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        history = self.get_history(session_id)

        if not history:
            return question.strip()

        recent_history = history[-4:]

        context_parts = []

        for message in recent_history:
            role = message["role"].upper()
            content = message["content"]

            context_parts.append(f"{role}: {content}")

        context_text = "\n".join(context_parts)

        return (
            f"Previous conversation:\n{context_text}\n\n"
            f"Current question: {question.strip()}"
        )

    def clear_history(self, session_id: str) -> None:
        """Clear conversation history for a session."""

        self._sessions.pop(session_id, None)

    def get_session_count(self) -> int:
        """Return the number of active conversation sessions."""

        return len(self._sessions)
