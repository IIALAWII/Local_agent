"""Memory router – POST /api/memory/store and POST /api/memory/search."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from memory_long import long_term_memory

router = APIRouter(prefix="/api/memory", tags=["memory"])


# ── Request / response models ─────────────────────────────────────────────────


class StoreRequest(BaseModel):
    """Request body for the memory store endpoint."""

    text: str = Field(..., description="Text content to embed and store.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional key-value metadata to attach.",
    )
    doc_id: str | None = Field(None, description="Optional explicit document ID.")


class StoreResponse(BaseModel):
    """Response from the memory store endpoint."""

    doc_id: str


class SearchRequest(BaseModel):
    """Request body for the memory search endpoint."""

    query: str = Field(..., description="Natural-language query string.")
    k: int = Field(5, ge=1, le=50, description="Number of results to return.")
    filter: dict[str, Any] | None = Field(
        None, description="Optional ChromaDB metadata filter."
    )


class SearchResult(BaseModel):
    """Single search result entry."""

    content: str
    metadata: dict[str, Any]
    score: float


class SearchResponse(BaseModel):
    """Response from the memory search endpoint."""

    results: list[SearchResult]


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/store", response_model=StoreResponse)
async def store_memory(request: StoreRequest) -> StoreResponse:
    """Embed *text* and store it in the long-term vector memory.

    Args:
        request: The store request body.

    Returns:
        The document ID assigned to the stored memory.
    """
    try:
        doc_id = long_term_memory.store(
            text=request.text,
            metadata=request.metadata,
            doc_id=request.doc_id,
        )
        return StoreResponse(doc_id=doc_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/search", response_model=SearchResponse)
async def search_memory(request: SearchRequest) -> SearchResponse:
    """Perform a semantic similarity search against the long-term memory.

    Args:
        request: The search request body.

    Returns:
        A ranked list of matching memory entries.
    """
    try:
        raw_results = long_term_memory.search(
            query=request.query,
            k=request.k,
            filter=request.filter,
        )
        results = [
            SearchResult(
                content=r["content"],
                metadata=r["metadata"],
                score=r["score"],
            )
            for r in raw_results
        ]
        return SearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
