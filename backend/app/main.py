from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.chains import AgentChain
from app.db.vectorstore_chroma import ChromaVectorStore
from app.llm.ollama_client import OllamaClient
from app.memory.memory_long import LongTermMemoryManager
from app.memory.memory_short import ShortTermMemoryManager


class ChatRequest(BaseModel):
	message: str = Field(min_length=1)
	session_id: str | None = None
	system_prompt: str | None = None


class MemoryStoreRequest(BaseModel):
	session_id: str
	text: str = Field(min_length=1)
	source: str = "manual"


class MemorySearchRequest(BaseModel):
	session_id: str
	query: str = Field(min_length=1)
	k: int = 5


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

short_memory = ShortTermMemoryManager()
try:
	vector_store = ChromaVectorStore(host=CHROMA_HOST, port=CHROMA_PORT)
except Exception:
	vector_store = None
long_memory = LongTermMemoryManager(vector_store=vector_store)
ollama_client = OllamaClient(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
agent_chain = AgentChain(
	ollama_client=ollama_client,
	short_memory=short_memory,
	long_memory=long_memory,
)

app = FastAPI(title="Local Agent Backend", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
	return {"status": "ok"}


@app.get("/api/sessions")
def list_sessions() -> dict:
	sessions = short_memory.list_sessions()
	return {"sessions": sessions}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
	session_id = request.session_id or str(uuid.uuid4())

	async def stream() -> AsyncIterator[str]:
		yield f"[SESSION_ID]{session_id}\n"
		try:
			async for chunk in agent_chain.stream_chat(
				session_id=session_id,
				user_message=request.message,
				system_prompt=request.system_prompt,
			):
				yield chunk
		except Exception as exc:
			yield f"\n[ERROR] Chat generation failed: {exc}"

	return StreamingResponse(stream(), media_type="text/plain")


@app.post("/api/memory/store")
def store_memory(request: MemoryStoreRequest) -> dict:
	try:
		memory_id = long_memory.store(
			session_id=request.session_id,
			text=request.text,
			source=request.source,
		)
		return {"id": memory_id, "status": "stored"}
	except Exception as exc:  # pragma: no cover
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/memory/search")
def search_memory(request: MemorySearchRequest) -> dict:
	try:
		results = long_memory.search(
			session_id=request.session_id,
			query=request.query,
			k=request.k,
		)
		return {"results": results}
	except Exception as exc:  # pragma: no cover
		raise HTTPException(status_code=500, detail=str(exc)) from exc

