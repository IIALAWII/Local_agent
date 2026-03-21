from __future__ import annotations


def list_upcoming_events(user_id: str) -> dict:
	return {
		"tool": "google_calendar",
		"status": "not_configured",
		"user_id": user_id,
		"message": "Google Calendar integration is scaffolded. Add OAuth credentials and API bindings.",
	}

