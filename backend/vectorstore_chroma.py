"""ChromaDB vector-store helpers shared across the application."""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings


def get_chroma_client() -> chromadb.HttpClient:
    """Return a configured ChromaDB HTTP client.

    Returns:
        An :class:`chromadb.HttpClient` pointed at the Docker-networked Chroma service.
    """
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_or_create_collection(
    client: chromadb.HttpClient,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> chromadb.Collection:
    """Return (or create) a ChromaDB collection by *name*.

    Args:
        client: An existing ChromaDB client instance.
        name: Collection name; defaults to :data:`settings.chroma_collection`.
        metadata: Optional metadata to attach when the collection is created.

    Returns:
        The :class:`chromadb.Collection` object.
    """
    return client.get_or_create_collection(
        name=name or settings.chroma_collection,
        metadata=metadata or {"hnsw:space": "cosine"},
    )


def upsert_documents(
    collection: chromadb.Collection,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict[str, Any]] | None = None,
    embeddings: list[list[float]] | None = None,
) -> None:
    """Upsert documents into a ChromaDB collection.

    Args:
        collection: Target ChromaDB collection.
        ids: Unique document IDs (must be the same length as *documents*).
        documents: Raw text content for each document.
        metadatas: Optional list of metadata dicts, one per document.
        embeddings: Optional pre-computed embedding vectors.
    """
    kwargs: dict[str, Any] = {"ids": ids, "documents": documents}
    if metadatas:
        kwargs["metadatas"] = metadatas
    if embeddings:
        kwargs["embeddings"] = embeddings
    collection.upsert(**kwargs)


def query_collection(
    collection: chromadb.Collection,
    query_texts: list[str],
    n_results: int = 5,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Query a ChromaDB collection using text similarity.

    Args:
        collection: The collection to query.
        query_texts: One or more natural-language query strings.
        n_results: How many nearest neighbours to return per query.
        where: Optional ChromaDB metadata filter.

    Returns:
        Raw ChromaDB query result dict containing ``ids``, ``documents``,
        ``distances``, and ``metadatas`` lists.
    """
    kwargs: dict[str, Any] = {
        "query_texts": query_texts,
        "n_results": n_results,
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)
