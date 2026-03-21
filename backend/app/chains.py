from __future__ import annotations

from collections.abc import AsyncIterator

from app.llm.ollama_client import OllamaClient
from app.memory.memory_long import LongTermMemoryManager
from app.memory.memory_short import ShortTermMemoryManager


class AgentChain:
	def __init__(
		self,
		ollama_client: OllamaClient,
		short_memory: ShortTermMemoryManager,
		long_memory: LongTermMemoryManager,
	) -> None:
		self.ollama_client = ollama_client
		self.short_memory = short_memory
		self.long_memory = long_memory

	async def stream_chat(
		self,
		session_id: str,
		user_message: str,
		system_prompt: str | None = None,
	) -> AsyncIterator[str]:
		session_memory = self.short_memory.get_or_create(session_id)
		history = session_memory.chat_memory.messages
		long_context = self.long_memory.search(session_id=session_id, query=user_message, k=3)

		history_text = "\n".join(
			f"{message.type.upper()}: {message.content}" for message in history[-10:]
		)
		long_text = "\n".join(item["text"] for item in long_context if item.get("text"))

		prompt = (
			"You are a local AI assistant. Use recent conversation and memory context when relevant.\n\n"
			f"Recent conversation:\n{history_text or '(none)'}\n\n"
			f"Long memory context:\n{long_text or '(none)'}\n\n"
			f"User: {user_message}"
		)

		chunks: list[str] = []
		async for token in self.ollama_client.stream_chat(prompt=prompt, system_prompt=system_prompt):
			chunks.append(token)
			yield token

		answer = "".join(chunks).strip()
		session_memory.chat_memory.add_user_message(user_message)
		session_memory.chat_memory.add_ai_message(answer)
		self.long_memory.store(session_id=session_id, text=f"User: {user_message}\nAssistant: {answer}")

