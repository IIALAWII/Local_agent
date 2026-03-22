"""Unit tests for the short-term memory module."""

from __future__ import annotations

from memory_short import SessionMemoryStore, ShortTermMemory


def test_short_term_memory_add_and_retrieve() -> None:
    """Messages added to a buffer are returned in order."""
    mem = ShortTermMemory(session_id="s1")
    mem.add_user_message("Hi")
    mem.add_ai_message("Hello!")

    messages = mem.get_messages()
    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "Hi"}
    assert messages[1] == {"role": "assistant", "content": "Hello!"}


def test_short_term_memory_clear() -> None:
    """Clearing a buffer removes all messages."""
    mem = ShortTermMemory(session_id="s2")
    mem.add_user_message("Hello")
    mem.clear()
    assert mem.message_count() == 0
    assert mem.get_messages() == []


def test_session_store_get_or_create() -> None:
    """The session store lazily creates memory instances."""
    store = SessionMemoryStore()
    mem1 = store.get_or_create("abc")
    mem2 = store.get_or_create("abc")
    assert mem1 is mem2  # Same instance returned


def test_session_store_list_and_delete() -> None:
    """Sessions can be listed and deleted."""
    store = SessionMemoryStore()
    store.get_or_create("x")
    store.get_or_create("y")

    assert set(store.list_sessions()) == {"x", "y"}

    store.delete("x")
    assert store.list_sessions() == ["y"]


def test_session_store_delete_nonexistent() -> None:
    """Deleting a missing session ID is a no-op."""
    store = SessionMemoryStore()
    store.delete("does-not-exist")  # Should not raise
