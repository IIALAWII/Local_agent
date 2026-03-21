"use client";

import { FormEvent, useState } from "react";

import { streamChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

type ChatWindowProps = {
	sessionId: string | null;
	systemPrompt: string;
	onSessionDetected: (sessionId: string) => void;
};

export default function ChatWindow({
	sessionId,
	systemPrompt,
	onSessionDetected,
}: ChatWindowProps) {
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [input, setInput] = useState("");
	const [isLoading, setIsLoading] = useState(false);

	const onSubmit = async (event: FormEvent) => {
		event.preventDefault();
		const message = input.trim();
		if (!message || isLoading) {
			return;
		}

		setInput("");
		setIsLoading(true);
		setMessages((previous) => [...previous, { role: "user", content: message }]);
		setMessages((previous) => [...previous, { role: "assistant", content: "" }]);

		try {
			await streamChat(
				{
					message,
					session_id: sessionId ?? undefined,
					system_prompt: systemPrompt || undefined,
				},
				(detectedSession) => {
					onSessionDetected(detectedSession);
				},
				(chunk) => {
					setMessages((previous) => {
						const updated = [...previous];
						const lastIndex = updated.length - 1;
						if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
							updated[lastIndex] = {
								...updated[lastIndex],
								content: `${updated[lastIndex].content}${chunk}`,
							};
						}
						return updated;
					});
				},
			);
		} catch (error) {
			const message = error instanceof Error ? error.message : "Unknown chat error";
			setMessages((previous) => {
				const updated = [...previous];
				const lastIndex = updated.length - 1;
				if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
					updated[lastIndex] = {
						...updated[lastIndex],
						content: `[error] ${message}`,
					};
				}
				return updated;
			});
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<section className="panel">
			<h2>Chat</h2>
			<div className="chat-log">
				{messages.length === 0 ? (
					<p className="muted">Start a conversation with the local AI agent.</p>
				) : (
					messages.map((item, index) => (
						<article key={`${item.role}-${index}`} className={`message ${item.role}`}>
							<strong>{item.role === "user" ? "You" : "Assistant"}</strong>
							<p>{item.content || "..."}</p>
						</article>
					))
				)}
			</div>
			<form className="chat-form" onSubmit={onSubmit}>
				<input
					value={input}
					onChange={(event) => setInput(event.target.value)}
					placeholder="Type your message"
					disabled={isLoading}
				/>
				<button type="submit" disabled={isLoading || !input.trim()}>
					{isLoading ? "Streaming..." : "Send"}
				</button>
			</form>
		</section>
	);
}
