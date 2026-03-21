"""Unit tests for the Ollama client (all HTTP calls are mocked)."""

from __future__ import annotations

import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ollama_client import OllamaClient


@pytest.fixture()
def client() -> OllamaClient:
    """Return an OllamaClient pointed at a dummy URL."""
    return OllamaClient(
        base_url="http://localhost:11434",
        model="test-model",
        temperature=0.5,
    )


@pytest.mark.asyncio
async def test_generate(client: OllamaClient) -> None:
    """generate() returns the 'response' field from Ollama."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Hi there!"}
    mock_response.raise_for_status = MagicMock()

    with patch("ollama_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_http

        result = await client.generate("Say hi")

    assert result == "Hi there!"


@pytest.mark.asyncio
async def test_chat(client: OllamaClient) -> None:
    """chat() returns the assistant message content."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": "I am fine."}
    }
    mock_response.raise_for_status = MagicMock()

    with patch("ollama_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_http

        result = await client.chat([{"role": "user", "content": "How are you?"}])

    assert result == "I am fine."


@pytest.mark.asyncio
async def test_list_models(client: OllamaClient) -> None:
    """list_models() returns model name strings."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [{"name": "llama3"}, {"name": "gpt-oss:20b"}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("ollama_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_http

        models = await client.list_models()

    assert models == ["llama3", "gpt-oss:20b"]
