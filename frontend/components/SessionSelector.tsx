"use client";

type SessionSelectorProps = {
	sessions: string[];
	selectedSession: string | null;
	onSelect: (sessionId: string) => void;
};

export default function SessionSelector({
	sessions,
	selectedSession,
	onSelect,
}: SessionSelectorProps) {
	return (
		<section className="panel">
			<h2>Sessions</h2>
			{sessions.length === 0 ? (
				<p className="muted">No sessions yet.</p>
			) : (
				<ul className="session-list">
					{sessions.map((sessionId) => (
						<li key={sessionId}>
							<button
								className={selectedSession === sessionId ? "active" : ""}
								onClick={() => onSelect(sessionId)}
								type="button"
							>
								{sessionId}
							</button>
						</li>
					))}
				</ul>
			)}
		</section>
	);
}
