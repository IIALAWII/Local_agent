from __future__ import annotations

from app.db.vectorstore_chroma import ChromaVectorStore


class LongTermMemoryManager:
	def __init__(self, vector_store: ChromaVectorStore | None) -> None:
		self.vector_store = vector_store

	def store(self, session_id: str, text: str, source: str = "chat") -> str:
		if self.vector_store is None:
			return "memory-disabled"
		return self.vector_store.add_text(session_id=session_id, text=text, source=source)

	def search(self, session_id: str, query: str, k: int = 5) -> list[dict]:
		if self.vector_store is None:
			return []
		return self.vector_store.search(session_id=session_id, query=query, k=k)

