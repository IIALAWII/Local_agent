import type { ChatRequest, SessionListResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001";

export async function fetchSessions(): Promise<string[]> {
	const response = await fetch(`${API_BASE}/api/sessions`, { cache: "no-store" });
	if (!response.ok) {
		throw new Error("Failed to load sessions");
	}

	const data = (await response.json()) as SessionListResponse;
	return data.sessions;
}

export async function streamChat(
	payload: ChatRequest,
	onSessionId: (sessionId: string) => void,
	onChunk: (chunk: string) => void,
): Promise<void> {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), 65000);

	let response: Response;
	try {
		response = await fetch(`${API_BASE}/api/chat`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(payload),
			signal: controller.signal,
		});
	} catch (error) {
		if (error instanceof Error && error.name === "AbortError") {
			throw new Error("Request timed out waiting for backend response.");
		}
		throw error;
	} finally {
		clearTimeout(timeoutId);
	}

	if (!response.ok || !response.body) {
		throw new Error("Failed to start stream");
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder("utf-8");
	let buffer = "";
	let sessionParsed = false;

	while (true) {
		const { done, value } = await reader.read();
		if (done) {
			if (buffer) {
				if (!sessionParsed && buffer.startsWith("[SESSION_ID]")) {
					const sessionId = buffer.replace("[SESSION_ID]", "").trim();
					if (sessionId) {
						onSessionId(sessionId);
					}
				} else {
					onChunk(buffer);
				}
			}
			break;
		}

		buffer += decoder.decode(value, { stream: true });

		if (!sessionParsed) {
			const newlineIndex = buffer.indexOf("\n");
			if (newlineIndex >= 0) {
				const firstLine = buffer.slice(0, newlineIndex);
				if (firstLine.startsWith("[SESSION_ID]")) {
					const sessionId = firstLine.replace("[SESSION_ID]", "").trim();
					if (sessionId) {
						onSessionId(sessionId);
					}
				}
				buffer = buffer.slice(newlineIndex + 1);
				sessionParsed = true;
			}
		}

		if (sessionParsed && buffer) {
			onChunk(buffer);
			buffer = "";
		}
	}
}
