/**
 * Typed API client for the FastAPI backend.
 * All functions throw on non-2xx responses.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ChatRequest {
  message: string;
  session_id?: string;
  stream?: boolean;
  model?: string;
  temperature?: number;
  use_agent?: boolean;
}

export interface ChatResponse {
  session_id: string;
  response: string;
}

export interface SessionInfo {
  session_id: string;
  message_count: number;
}

export interface SessionList {
  sessions: SessionInfo[];
}

export interface StoreMemoryRequest {
  text: string;
  metadata?: Record<string, unknown>;
  doc_id?: string;
}

export interface StoreMemoryResponse {
  doc_id: string;
}

export interface SearchMemoryRequest {
  query: string;
  k?: number;
  filter?: Record<string, unknown>;
}

export interface SearchResult {
  content: string;
  metadata: Record<string, unknown>;
  score: number;
}

export interface SearchMemoryResponse {
  results: SearchResult[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ── Chat ─────────────────────────────────────────────────────────────────────

/**
 * Send a chat message (non-streaming).
 */
export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ ...req, stream: false }),
  });
}

/**
 * Send a chat message and stream back the response tokens.
 * The callback is invoked for each token; resolves when the stream ends.
 */
export async function sendChatStream(
  req: ChatRequest,
  onToken: (token: string) => void,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...req, stream: true }),
  });

  if (!res.ok || !res.body) {
    const body = await res.text();
    throw new Error(`Stream error ${res.status}: ${body}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const json = line.slice(6).trim();
      if (!json) continue;
      try {
        const chunk = JSON.parse(json) as { token?: string; done?: boolean };
        if (chunk.token) onToken(chunk.token);
        if (chunk.done) return;
      } catch {
        // Ignore malformed JSON lines
      }
    }
  }
}

// ── Sessions ─────────────────────────────────────────────────────────────────

export async function getSessions(): Promise<SessionList> {
  return apiFetch<SessionList>('/api/sessions');
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${BASE_URL}/api/sessions/${sessionId}`, { method: 'DELETE' });
}

// ── Memory ────────────────────────────────────────────────────────────────────

export async function storeMemory(
  req: StoreMemoryRequest,
): Promise<StoreMemoryResponse> {
  return apiFetch<StoreMemoryResponse>('/api/memory/store', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function searchMemory(
  req: SearchMemoryRequest,
): Promise<SearchMemoryResponse> {
  return apiFetch<SearchMemoryResponse>('/api/memory/search', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}
