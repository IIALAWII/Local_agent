export type ChatMessage = {
	role: "user" | "assistant";
	content: string;
};

export type ChatRequest = {
	message: string;
	session_id?: string;
	system_prompt?: string;
};

export type SessionListResponse = {
	sessions: string[];
};

export type MemorySearchResult = {
	id: string;
	text: string;
	metadata: Record<string, string>;
	score: number;
};
