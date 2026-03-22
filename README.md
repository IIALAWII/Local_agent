# Local_agent

Full-stack local AI agent system with:
- Backend: FastAPI + LangChain + Ollama (`gpt-oss:20b`)
- Frontend: Next.js (chat streaming, sessions, settings, Google OAuth UI)
- Long-term memory: ChromaDB (Docker)
- Infra: Docker Compose

## Quick Start (How to Run)

Follow these steps in order to start the application:

### Step 1 — Install prerequisites

- Install **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (includes Docker Compose).
- Install **[Ollama](https://ollama.com/download)** on your host machine (the machine running Docker, not inside a container).

### Step 2 — Pull the AI model and start Ollama

Open a terminal on your **host machine** and run:

```bash
ollama pull gpt-oss:20b
ollama serve
```

> Keep this terminal open. Ollama must stay running while the app is in use.

Verify Ollama is reachable:

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response listing available models.

### Step 3 — Start the application stack

Open a **new terminal**, navigate to the project folder, then run:

```bash
cd infra
docker compose up --build
```

This builds and starts three services:
| Service | URL |
|---------|-----|
| Frontend (chat UI) | http://localhost:3000 |
| Backend (API) | http://localhost:8001 |
| ChromaDB (vector memory) | http://localhost:8000 |

Wait for all three containers to print that they are ready (look for `Uvicorn running` from the backend and `ready started server` from the frontend), then open **http://localhost:3000** in your browser.

### Step 4 — Verify everything is working

Run these smoke-test commands in a terminal:

```bash
# Backend health check
curl http://localhost:8001/health

# List sessions
curl http://localhost:8001/api/sessions

# Send a test chat message (streaming)
curl -N -X POST http://localhost:8001/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Reply with exactly: smoke-ok","session_id":"smoke-session"}'
```

The chat command should stream back a `[SESSION_ID]...` header followed by model tokens. If only the session header appears and no tokens, check that Ollama is still running on the host (`ollama serve`).

### Stopping the application

```bash
# In the infra/ directory
docker compose down
```

---

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

## CI

GitHub Actions workflow in `.github/workflows/ci.yml` runs:
- backend dependency install + import check
- frontend dependency install + production build
