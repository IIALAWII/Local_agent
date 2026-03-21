from __future__ import annotations


def get_recent_emails(user_id: str) -> dict:
	return {
		"tool": "gmail",
		"status": "not_configured",
		"user_id": user_id,
		"message": "Gmail integration is scaffolded. Add Google OAuth tokens to enable real API calls.",
	}

