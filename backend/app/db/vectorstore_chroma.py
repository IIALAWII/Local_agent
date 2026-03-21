from __future__ import annotations

import uuid
from collections import Counter

import chromadb


def _score_overlap(query: str, candidate: str) -> int:
	query_tokens = Counter(token.lower() for token in query.split())
	candidate_tokens = Counter(token.lower() for token in candidate.split())
	return sum((query_tokens & candidate_tokens).values())


class ChromaVectorStore:
	def __init__(self, host: str, port: int, collection_name: str = "agent_memory") -> None:
		self.client = chromadb.HttpClient(host=host, port=port)
		self.collection = self.client.get_or_create_collection(name=collection_name)

	def add_text(self, session_id: str, text: str, source: str = "chat") -> str:
		doc_id = str(uuid.uuid4())
		self.collection.add(
			ids=[doc_id],
			documents=[text],
			metadatas=[{"session_id": session_id, "source": source}],
		)
		return doc_id

	def search(self, session_id: str, query: str, k: int = 5) -> list[dict]:
		results = self.collection.get(
			where={"session_id": session_id},
			include=["documents", "metadatas"],
		)

		documents = results.get("documents") or []
		metadatas = results.get("metadatas") or []
		ids = results.get("ids") or []

		ranked = []
		for doc_id, doc, metadata in zip(ids, documents, metadatas, strict=False):
			if not doc:
				continue
			score = _score_overlap(query, doc)
			ranked.append(
				{
					"id": doc_id,
					"text": doc,
					"metadata": metadata or {},
					"score": score,
				}
			)

		ranked.sort(key=lambda item: item["score"], reverse=True)
		return ranked[:k]

