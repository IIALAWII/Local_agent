from __future__ import annotations


def list_drive_files(user_id: str) -> dict:
	return {
		"tool": "google_drive",
		"status": "not_configured",
		"user_id": user_id,
		"message": "Google Drive integration is scaffolded. Add OAuth credentials and Drive API client.",
	}

