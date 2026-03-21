"use client";

import { useCallback, useEffect, useState } from "react";

import ChatWindow from "@/components/ChatWindow";
import GoogleLoginButton from "@/components/GoogleLoginButton";
import SessionSelector from "@/components/SessionSelector";
import SettingsPanel from "@/components/SettingsPanel";
import { fetchSessions } from "@/lib/api";

export default function HomePage() {
	const [sessions, setSessions] = useState<string[]>([]);
	const [selectedSession, setSelectedSession] = useState<string | null>(null);
	const [systemPrompt, setSystemPrompt] = useState("");
	const [googleToken, setGoogleToken] = useState<string | null>(null);

	const loadSessions = useCallback(async () => {
		try {
			const data = await fetchSessions();
			setSessions(data);
			if (data.length > 0 && !selectedSession) {
				setSelectedSession(data[0]);
			}
		} catch {
			setSessions([]);
		}
	}, [selectedSession]);

	useEffect(() => {
		void loadSessions();
	}, [loadSessions]);

	const handleSessionDetected = (sessionId: string) => {
		setSelectedSession(sessionId);
		setSessions((previous) => {
			if (previous.includes(sessionId)) {
				return previous;
			}
			return [sessionId, ...previous];
		});
	};

	return (
		<main className="container">
			<header>
				<h1>Local AI Agent</h1>
				<p>FastAPI + LangChain + Ollama (gpt-oss:20b) + ChromaDB</p>
			</header>
			<section className="grid">
				<div className="column">
					<SessionSelector
						sessions={sessions}
						selectedSession={selectedSession}
						onSelect={setSelectedSession}
					/>
					<GoogleLoginButton onToken={setGoogleToken} />
					{googleToken && <p className="token-ok">Google login connected.</p>}
				</div>
				<ChatWindow
					sessionId={selectedSession}
					systemPrompt={systemPrompt}
					onSessionDetected={handleSessionDetected}
				/>
				<SettingsPanel
					systemPrompt={systemPrompt}
					onSystemPromptChange={setSystemPrompt}
				/>
			</section>
		</main>
	);
}
