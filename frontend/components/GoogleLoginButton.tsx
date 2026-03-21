"use client";

import { useEffect, useRef, useState } from "react";

declare global {
	interface Window {
		google?: {
			accounts: {
				id: {
					initialize: (args: {
						client_id: string;
						callback: (response: { credential: string }) => void;
					}) => void;
					renderButton: (
						element: HTMLElement,
						options: { theme: "outline"; size: "large"; width?: number },
					) => void;
				};
			};
		};
	}
}

type GoogleLoginButtonProps = {
	onToken: (token: string) => void;
};

export default function GoogleLoginButton({ onToken }: GoogleLoginButtonProps) {
	const containerRef = useRef<HTMLDivElement | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
		if (!clientId) {
			setError("Set NEXT_PUBLIC_GOOGLE_CLIENT_ID to enable Google OAuth.");
			return;
		}

		const script = document.createElement("script");
		script.src = "https://accounts.google.com/gsi/client";
		script.async = true;
		script.defer = true;

		script.onload = () => {
			if (!window.google || !containerRef.current) {
				setError("Google SDK failed to load.");
				return;
			}

			window.google.accounts.id.initialize({
				client_id: clientId,
				callback: (response) => {
					if (response.credential) {
						onToken(response.credential);
					}
				},
			});

			window.google.accounts.id.renderButton(containerRef.current, {
				theme: "outline",
				size: "large",
				width: 280,
			});
		};

		document.body.appendChild(script);

		return () => {
			if (script.parentNode) {
				script.parentNode.removeChild(script);
			}
		};
	}, [onToken]);

	return (
		<section className="panel">
			<h2>Google OAuth</h2>
			<div ref={containerRef} />
			{error && <p className="muted">{error}</p>}
		</section>
	);
}
