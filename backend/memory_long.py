"""Long-term semantic memory backed by ChromaDB via LangChain embeddings."""

from __future__ import annotations

import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from config import settings


def _build_chroma_client() -> chromadb.HttpClient:
    """Create a ChromaDB HTTP client pointed at the configured host.

    Returns:
        An authenticated :class:`chromadb.HttpClient` instance.
    """
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _build_embeddings() -> OllamaEmbeddings:
    """Create an Ollama-backed embeddings model.

    Returns:
        A :class:`OllamaEmbeddings` instance pointing at the local Ollama server.
    """
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )


class LongTermMemory:
    """Semantic vector store for persisting and retrieving agent memories.

    Uses ChromaDB as the backend and Ollama for generating text embeddings,
    so no external embedding API is required.
    """

    def __init__(self) -> None:
        self._client = _build_chroma_client()
        self._embeddings = _build_embeddings()
        self._vectorstore = Chroma(
            client=self._client,
            collection_name=settings.chroma_collection,
            embedding_function=self._embeddings,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def store(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        """Embed *text* and persist it to the vector store.

        Args:
            text: The text to embed and store.
            metadata: Optional key-value pairs to attach to the document.
            doc_id: Optional explicit document ID; a UUID is generated if absent.

        Returns:
            The document ID that was used to store the entry.
        """
        doc_id = doc_id or str(uuid.uuid4())
        self._vectorstore.add_texts(
            texts=[text],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )
        return doc_id

    def search(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform a semantic similarity search against stored memories.

        Args:
            query: Natural-language search query.
            k: Maximum number of results to return.
            filter: Optional ChromaDB metadata filter dict.

        Returns:
            List of dicts with ``content`` and ``metadata`` keys, ranked by
            similarity (most similar first).
        """
        kwargs: dict[str, Any] = {"k": k}
        if filter:
            kwargs["filter"] = filter

        results = self._vectorstore.similarity_search_with_relevance_scores(
            query, **kwargs
        )
        return [
            {"content": doc.page_content, "metadata": doc.metadata, "score": score}
            for doc, score in results
        ]

    def delete(self, doc_id: str) -> None:
        """Remove a single document from the vector store by its ID.

        Args:
            doc_id: The document ID to delete.
        """
        self._vectorstore._collection.delete(ids=[doc_id])

    def count(self) -> int:
        """Return the total number of documents in the collection.

        Returns:
            Integer document count.
        """
        return self._vectorstore._collection.count()


# Module-level singleton (lazy – constructed on first import)
long_term_memory = LongTermMemory()
