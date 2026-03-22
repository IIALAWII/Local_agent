"""Shared Google OAuth2 credential helper used by all Google API tools."""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


# Scopes required by all integrated Google services
_SCOPES: list[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
]

_TOKEN_PATH = Path("token.json")
_CREDENTIALS_PATH = Path("credentials.json")


def get_google_credentials() -> Credentials:
    """Load or refresh Google OAuth2 credentials.

    On the first run the user is sent through the browser OAuth2 flow.
    Subsequent runs reload the saved token from ``token.json`` and refresh it
    automatically when it has expired.

    Returns:
        A valid :class:`google.oauth2.credentials.Credentials` object.

    Raises:
        FileNotFoundError: If ``credentials.json`` is missing on a first-time run.
    """
    creds: Credentials | None = None

    # Try to load a previously stored token
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), _SCOPES)

    # Refresh or re-authorise as needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_CREDENTIALS_PATH), _SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Persist for next run
        _TOKEN_PATH.write_text(creds.to_json())

    return creds
