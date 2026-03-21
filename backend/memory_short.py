"""Short-term (in-process) conversation memory backed by LangChain."""

from __future__ import annotations

from typing import Any

from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage


class ShortTermMemory:
    """Per-session conversation buffer that keeps the full message history.

    Each instance corresponds to one chat session identified by *session_id*.
    Instances should be cached externally (e.g. in a dict) so that memory
    survives across requests within a process lifetime.
    """

    def __init__(self, session_id: str) -> None:
        """Initialise a new buffer for *session_id*.

        Args:
            session_id: Unique identifier for the chat session.
        """
        self.session_id = session_id
        self._memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def add_user_message(self, content: str) -> None:
        """Append a human turn to the buffer.

        Args:
            content: The user's message text.
        """
        self._memory.chat_memory.add_user_message(content)

    def add_ai_message(self, content: str) -> None:
        """Append an AI turn to the buffer.

        Args:
            content: The assistant's response text.
        """
        self._memory.chat_memory.add_ai_message(content)

    def get_messages(self) -> list[dict[str, str]]:
        """Return all messages as a list of ``{"role": ..., "content": ...}`` dicts.

        Returns:
            Ordered list of message dicts compatible with the Ollama chat API.
        """
        messages: list[dict[str, str]] = []
        for msg in self._memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        return messages

    def get_variables(self) -> dict[str, Any]:
        """Return LangChain memory variables (useful for chain integration).

        Returns:
            Dict containing ``chat_history`` key with message objects.
        """
        return self._memory.load_memory_variables({})

    def clear(self) -> None:
        """Remove all messages from this session's buffer."""
        self._memory.clear()

    def message_count(self) -> int:
        """Return the total number of messages stored.

        Returns:
            Integer count of messages (user + assistant combined).
        """
        return len(self._memory.chat_memory.messages)


class SessionMemoryStore:
    """Simple registry that lazily creates and caches :class:`ShortTermMemory` instances."""

    def __init__(self) -> None:
        self._sessions: dict[str, ShortTermMemory] = {}

    def get_or_create(self, session_id: str) -> ShortTermMemory:
        """Return existing memory for *session_id*, creating it if absent.

        Args:
            session_id: Unique session identifier.

        Returns:
            The :class:`ShortTermMemory` instance for the session.
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = ShortTermMemory(session_id)
        return self._sessions[session_id]

    def delete(self, session_id: str) -> None:
        """Remove the memory associated with *session_id*, if present.

        Args:
            session_id: Session to remove.
        """
        self._sessions.pop(session_id, None)

    def list_sessions(self) -> list[str]:
        """Return a list of all tracked session IDs.

        Returns:
            List of session ID strings.
        """
        return list(self._sessions.keys())


# Module-level singleton used by routers and chains
session_store = SessionMemoryStore()
