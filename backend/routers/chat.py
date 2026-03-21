"""Chat router – POST /api/chat with optional SSE streaming."""

from __future__ import annotations

import uuid
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from chains import run_agent
from memory_short import session_store
from ollama_client import OllamaClient

router = APIRouter(prefix="/api", tags=["chat"])


# ── Request / response models ─────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    message: str = Field(..., description="User message text.")
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Chat session identifier. A new UUID is generated if omitted.",
    )
    stream: bool = Field(False, description="When true, responses are streamed as SSE.")
    model: str | None = Field(None, description="Override the default Ollama model.")
    temperature: float | None = Field(None, description="Sampling temperature (0–1).")
    use_agent: bool = Field(
        True,
        description=(
            "When true the full LangChain agent (with tools) is used. "
            "When false a plain Ollama chat call is made."
        ),
    )


class ChatResponse(BaseModel):
    """Response body for non-streaming chat requests."""

    session_id: str
    response: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse | StreamingResponse:
    """Send a message and receive an AI response.

    When ``stream=true`` the response is delivered as Server-Sent Events
    (``text/event-stream``). Each event contains a JSON chunk ``{"token": "…"}``.
    A final event ``{"done": true}`` marks the end of the stream.

    Args:
        request: The chat request body.

    Returns:
        A :class:`ChatResponse` for non-streaming requests, or a
        :class:`StreamingResponse` for streaming requests.
    """
    memory = session_store.get_or_create(request.session_id)
    memory.add_user_message(request.message)

    if request.stream:
        return StreamingResponse(
            _stream_tokens(request, memory),
            media_type="text/event-stream",
        )

    # Non-streaming path
    if request.use_agent:
        answer = await run_agent(
            request.message,
            memory,
            model=request.model,
            temperature=request.temperature,
        )
    else:
        client = OllamaClient(model=request.model, temperature=request.temperature)
        messages = memory.get_messages()
        answer = await client.chat(messages)

    memory.add_ai_message(answer)
    return ChatResponse(session_id=request.session_id, response=answer)


async def _stream_tokens(request: ChatRequest, memory: object) -> AsyncIterator[str]:
    """Generate SSE events from the Ollama streaming API.

    Args:
        request: The original chat request.
        memory: The session's short-term memory (any object with
            ``get_messages`` and ``add_ai_message`` methods).

    Yields:
        SSE-formatted byte strings.
    """
    client = OllamaClient(model=request.model, temperature=request.temperature)
    messages = memory.get_messages()  # type: ignore[union-attr]
    full_response = ""

    async for token in client.chat_stream(messages):
        full_response += token
        yield f'data: {{"token": {token!r}}}\n\n'

    memory.add_ai_message(full_response)  # type: ignore[union-attr]
    yield 'data: {"done": true}\n\n'
