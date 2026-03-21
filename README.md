# Local_agent

Full-stack local AI agent system with:
- Backend: FastAPI + LangChain + Ollama (`gpt-oss:20b`)
- Frontend: Next.js (chat streaming, sessions, settings, Google OAuth UI)
- Long-term memory: ChromaDB (Docker)
- Infra: Docker Compose

## Architecture

- `backend/` serves API + orchestration logic:
	- LLM client to Ollama over HTTP
	- Short memory via `ConversationBufferMemory`
	- Long memory persisted in Chroma collection
	- API routes for chat/sessions/memory store/search
- `frontend/` provides interactive UI:
	- Streaming chat rendering
	- Session list and selection
	- Settings panel for system prompt
	- Google OAuth UI token capture
- `infra/` runs deployment stack with 3 services:
	- `chroma` (`chromadb/chroma`)
	- `backend` (FastAPI app)
	- `frontend` (Next.js app)

## Runtime Data Flow

1. Frontend calls `POST /api/chat`.
2. Backend emits `[SESSION_ID]{id}` first line.
3. Backend chain composes prompt using:
	 - recent short-term chat history
	 - top long-memory snippets from Chroma
4. Backend streams Ollama tokens back to frontend.
5. On completion, backend stores turn pair in:
	 - short-term memory session buffer
	 - long-term Chroma store

## Services

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8001`
- ChromaDB: `http://localhost:8000`

## Prerequisites

- Docker + Docker Compose
- Ollama running on host machine with model pulled:

```bash
ollama pull gpt-oss:20b
ollama serve
```

## Run with Docker Compose

```bash
cd infra
docker compose up --build
```

Backend talks to host Ollama via `http://host.docker.internal:11434`.

## Required Ollama Host Setup

Run on host machine (outside containers):

```bash
ollama pull gpt-oss:20b
ollama serve
```

Quick host verification:

```bash
curl http://localhost:11434/api/tags
```

## Backend API

- `POST /api/chat` (streaming text response)
- `GET /api/sessions`
- `POST /api/memory/store`
- `POST /api/memory/search`

### `POST /api/chat`

Request JSON:

```json
{
	"message": "hello",
	"session_id": "optional",
	"system_prompt": "optional"
}
```

Response stream:
- first line: `[SESSION_ID]{session-id}`
- then model token chunks
- on backend failure: final chunk contains `[ERROR] ...`

## Frontend environment

Optional Google OAuth in UI:

```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
```

If `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is not set, login button remains disabled with guidance.

## Reliability Behavior

- Backend chat stream catches runtime errors and emits `[ERROR]` text instead of leaving stream open.
- Ollama HTTP client has explicit connect/read/write/pool timeouts to avoid long hangs.
- Frontend stream call has request timeout and shows error text in chat panel.

## Smoke Test

```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/sessions
curl -N -X POST http://localhost:8001/api/chat \
	-H 'Content-Type: application/json' \
	-d '{"message":"Reply with exactly: smoke-ok","session_id":"smoke-session"}'
```

If chat returns only `[SESSION_ID]...` and no tokens, Ollama host service is likely not reachable from Docker.

## CI

GitHub Actions workflow in `.github/workflows/ci.yml` runs:
- backend dependency install + import check
- frontend dependency install + production build
