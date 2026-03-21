"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import chat, memory, sessions

app = FastAPI(
    title="Local AI Agent",
    description=(
        "A local AI agent powered by Ollama, LangChain, and ChromaDB with "
        "Gmail, Google Calendar, and Google Drive integrations."
    ),
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(memory.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> dict[str, str]:
    """Basic liveness probe.

    Returns:
        A dict with ``status: ok``.
    """
    return {"status": "ok"}
