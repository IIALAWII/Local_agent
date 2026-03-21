from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx


class OllamaClient:
	def __init__(self, base_url: str, model: str = "gpt-oss:20b") -> None:
		self.base_url = base_url.rstrip("/")
		self.model = model

	async def stream_chat(
		self,
		prompt: str,
		system_prompt: str | None = None,
	) -> AsyncIterator[str]:
		payload = {
			"model": self.model,
			"stream": True,
			"messages": [],
		}

		if system_prompt:
			payload["messages"].append({"role": "system", "content": system_prompt})

		payload["messages"].append({"role": "user", "content": prompt})

		timeout = httpx.Timeout(connect=8.0, read=45.0, write=20.0, pool=8.0)
		async with httpx.AsyncClient(timeout=timeout) as client:
			async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
				response.raise_for_status()
				async for line in response.aiter_lines():
					if not line:
						continue

					try:
						data = json.loads(line)
					except json.JSONDecodeError:
						continue

					message = data.get("message") or {}
					content = message.get("content")
					if content:
						yield content

