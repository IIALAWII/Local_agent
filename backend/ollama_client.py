"""Async HTTP client for communicating with a local Ollama instance."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from config import settings


class OllamaClient:
    """Thin async wrapper around the Ollama REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature

    # ── Public helpers ────────────────────────────────────────────────────────

    async def generate(self, prompt: str, stream: bool = False) -> str:
        """Send a single prompt to Ollama and return the complete response text.

        Args:
            prompt: The raw text prompt to send.
            stream: Whether to stream the response (unused in non-streaming mode).

        Returns:
            The model's response as a plain string.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
    ) -> str:
        """Send a chat conversation to Ollama and return the assistant reply.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            stream: When *True* the generator variant should be used instead.

        Returns:
            The assistant message content as a plain string.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """Stream chat tokens from Ollama one chunk at a time.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.

        Yields:
            Incremental text tokens as they arrive from the model.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": self.temperature},
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break

    async def list_models(self) -> list[str]:
        """Return the names of all models available in this Ollama instance.

        Returns:
            A list of model name strings.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
