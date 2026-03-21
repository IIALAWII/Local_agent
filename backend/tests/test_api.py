"""Unit tests for the FastAPI application routes.

These tests use a fully mocked Ollama client and ChromaDB so that no external
services are required during CI.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure the backend package root is on the path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_client() -> TestClient:
    """Return a synchronous FastAPI test client with mocked external deps."""
    # Patch chromadb at the lowest level so the module-level singleton
    # never attempts a real network connection.
    mock_chroma_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_chroma_client.get_or_create_collection.return_value = mock_collection

    with (
        patch("chromadb.HttpClient", return_value=mock_chroma_client),
        patch("langchain_community.embeddings.OllamaEmbeddings.__init__", return_value=None),
        patch("langchain_community.vectorstores.Chroma.__init__", return_value=None),
        patch("langchain_community.llms.Ollama.__init__", return_value=None),
    ):
        # Force re-import so the singleton is created with patched deps
        import importlib
        import memory_long
        importlib.reload(memory_long)

        from main import app  # noqa: PLC0415
        return TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient with mocked ChromaDB and Ollama."""
    return _make_client()


# ── Health ─────────────────────────────────────────────────────────────────────


def test_health(client: TestClient) -> None:
    """GET /health must return 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Sessions ──────────────────────────────────────────────────────────────────


def test_list_sessions_empty(client: TestClient) -> None:
    """GET /api/sessions returns an empty list when no sessions exist."""
    # Patch the session store to appear empty
    with patch("routers.sessions.session_store") as mock_store:
        mock_store.list_sessions.return_value = []
        response = client.get("/api/sessions")

    assert response.status_code == 200
    assert response.json() == {"sessions": []}


def test_delete_session(client: TestClient) -> None:
    """DELETE /api/sessions/{id} returns 204."""
    with patch("routers.sessions.session_store") as mock_store:
        mock_store.delete.return_value = None
        response = client.delete("/api/sessions/test-session-id")

    assert response.status_code == 204


# ── Memory ────────────────────────────────────────────────────────────────────


def test_memory_store(client: TestClient) -> None:
    """POST /api/memory/store returns the document ID."""
    with patch("routers.memory.long_term_memory") as mock_mem:
        mock_mem.store.return_value = "doc-123"
        response = client.post(
            "/api/memory/store",
            json={"text": "Remember this fact.", "metadata": {"source": "test"}},
        )

    assert response.status_code == 200
    assert response.json() == {"doc_id": "doc-123"}


def test_memory_search(client: TestClient) -> None:
    """POST /api/memory/search returns ranked results."""
    with patch("routers.memory.long_term_memory") as mock_mem:
        mock_mem.search.return_value = [
            {"content": "A fact", "metadata": {}, "score": 0.9}
        ]
        response = client.post(
            "/api/memory/search",
            json={"query": "some query", "k": 3},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["content"] == "A fact"
    assert data["results"][0]["score"] == pytest.approx(0.9)


# ── Chat (non-streaming) ──────────────────────────────────────────────────────


def test_chat_non_streaming(client: TestClient) -> None:
    """POST /api/chat (non-streaming) returns a response string."""
    with (
        patch("routers.chat.run_agent", new_callable=AsyncMock) as mock_agent,
        patch("routers.chat.session_store") as mock_store,
    ):
        mock_memory = MagicMock()
        mock_memory.get_messages.return_value = []
        mock_store.get_or_create.return_value = mock_memory
        mock_agent.return_value = "Hello, how can I help?"

        response = client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "session_id": "test-session",
                "stream": False,
                "use_agent": True,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session"
    assert data["response"] == "Hello, how can I help?"
