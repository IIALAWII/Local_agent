import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
	title: "Local AI Agent",
	description: "Full-stack local AI agent with FastAPI + Ollama + Chroma",
};

export default function RootLayout({ children }: { children: ReactNode }) {
	return (
		<html lang="en">
			<body>{children}</body>
		</html>
	);
}
