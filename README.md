# Local AI Agent

A full-stack, locally-hosted AI agent system powered by **Ollama**, **LangChain**, **ChromaDB**, and **Next.js**. Designed for high-end hardware (RTX 4090 / i9-14900K / 32 GB DDR5).

```
ai-agent/
├── backend/          FastAPI + LangChain + Ollama + Google APIs
├── frontend/         Next.js chat UI with streaming support
├── infra/            docker-compose.yml (backend + frontend + ChromaDB)
└── .github/workflows/  CI/CD for backend tests, frontend build, and local deploy
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| Docker & Docker Compose | Latest |
| [Ollama](https://ollama.com) | Latest (runs on host, **not** in Docker) |
| Google Cloud project | With Gmail, Calendar, Drive APIs enabled |

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd Local_agent

# Backend config
cp backend/.env.example backend/.env
# Edit backend/.env – fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, etc.

# Frontend config
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local – same Google credentials + NEXTAUTH_SECRET
```

### 2. Install and pull the Ollama model (on host)

```bash
# Install Ollama: https://ollama.com/download
ollama pull gpt-oss:20b
```

### 3. Google API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Create or select a project, enable **Gmail API**, **Google Calendar API**, **Google Drive API**.
3. Create an **OAuth 2.0 Client ID** (Desktop app type).
4. Download the JSON → save as `backend/credentials.json`.
5. On first run the backend will open a browser for consent; the token is saved to `backend/token.json`.

### 4. Start all services with Docker Compose

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

This starts:
- **ChromaDB** on `localhost:8001`
- **Backend (FastAPI)** on `localhost:8000`
- **Frontend (Next.js)** on `localhost:3000`

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Running locally without Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### ChromaDB (Docker)

```bash
docker run -d -p 8001:8000 --name chromadb chromadb/chroma:latest
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message; supports streaming via SSE |
| `GET` | `/api/sessions` | List active chat sessions |
| `DELETE` | `/api/sessions/{id}` | Delete a session |
| `POST` | `/api/memory/store` | Store text in long-term vector memory |
| `POST` | `/api/memory/search` | Semantic search over long-term memory |
| `GET` | `/health` | Liveness probe |

### Example: chat request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List my unread emails", "use_agent": true}'
```

### Streaming chat (SSE)

```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a joke", "stream": true, "use_agent": false}'
```

---

## Running Tests

```bash
# Backend unit tests
cd backend
pip install -r requirements.txt pytest pytest-asyncio
pytest tests/ -v
```

---

## CI/CD

Three GitHub Actions workflows are included:

| Workflow | Trigger | What it does |
|---|---|---|
| `backend.yml` | Push/PR to `backend/` | Lint (Ruff) + pytest |
| `frontend.yml` | Push/PR to `frontend/` | ESLint + tsc + `next build` |
| `deploy.yml` | Manual dispatch | Pulls & restarts containers on a self-hosted runner |

To use the self-hosted deploy workflow, register a GitHub Actions runner on your local machine and set the `runs-on: self-hosted` label.

---

## Architecture

```
Browser (Next.js)
       │  HTTP / SSE
       ▼
FastAPI backend  ──► Ollama (host)   gpt-oss:20b
       │
       ├──► ConversationBufferMemory  (in-process, per session)
       │
       ├──► ChromaDB (Docker)         long-term semantic memory
       │
       └──► Google APIs               Gmail · Calendar · Drive
```

---

## Hardware recommendation

| Component | Recommended |
|---|---|
| GPU | NVIDIA RTX 4090 (24 GB VRAM) |
| CPU | Intel i9-14900K |
| RAM | 32 GB DDR5 |
| Storage | NVMe SSD (for model weights) |
