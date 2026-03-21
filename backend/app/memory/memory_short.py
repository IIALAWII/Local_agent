from __future__ import annotations

from langchain.memory import ConversationBufferMemory


class ShortTermMemoryManager:
	def __init__(self) -> None:
		self._sessions: dict[str, ConversationBufferMemory] = {}

	def get_or_create(self, session_id: str) -> ConversationBufferMemory:
		if session_id not in self._sessions:
			self._sessions[session_id] = ConversationBufferMemory(
				memory_key="history",
				return_messages=True,
			)
		return self._sessions[session_id]

	def list_sessions(self) -> list[str]:
		return sorted(self._sessions.keys())

