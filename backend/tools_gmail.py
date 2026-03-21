"""Gmail tool for the LangChain agent.

Provides read-only and send capabilities via the Gmail API using OAuth2
credentials previously obtained and stored as a token file.
"""

from __future__ import annotations

import base64
import email as email_lib
from email.mime.text import MIMEText
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tools_google_auth import get_google_credentials


def _gmail_service() -> Any:
    """Build and return an authenticated Gmail API service object.

    Returns:
        A :mod:`googleapiclient` resource for the Gmail API v1.
    """
    creds = get_google_credentials()
    return build("gmail", "v1", credentials=creds)


# ── Read helpers ──────────────────────────────────────────────────────────────


def list_messages(
    max_results: int = 10,
    query: str = "",
    label_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """List messages in the authenticated user's mailbox.

    Args:
        max_results: Maximum number of message stubs to return.
        query: Gmail search query string (e.g. ``"is:unread from:boss@example.com"``).
        label_ids: Optional list of label IDs to filter by (e.g. ``["INBOX"]``).

    Returns:
        List of dicts with ``id`` and ``threadId`` fields.
    """
    service = _gmail_service()
    params: dict[str, Any] = {"userId": "me", "maxResults": max_results}
    if query:
        params["q"] = query
    if label_ids:
        params["labelIds"] = label_ids

    result = service.users().messages().list(**params).execute()
    return result.get("messages", [])


def get_message(message_id: str) -> dict[str, Any]:
    """Fetch a single Gmail message by its ID.

    Args:
        message_id: The Gmail message ID.

    Returns:
        Dict containing ``subject``, ``from``, ``to``, ``date``, and ``body`` keys.
    """
    service = _gmail_service()
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
    body = _extract_body(msg["payload"])

    return {
        "id": message_id,
        "subject": headers.get("Subject", ""),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "date": headers.get("Date", ""),
        "body": body,
    }


def _extract_body(payload: dict[str, Any]) -> str:
    """Recursively extract plain-text body from a Gmail message payload.

    Args:
        payload: The ``payload`` portion of a Gmail message resource.

    Returns:
        Decoded plain-text body string.
    """
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    parts = payload.get("parts", [])
    for part in parts:
        body = _extract_body(part)
        if body:
            return body
    return ""


# ── Write helpers ─────────────────────────────────────────────────────────────


def send_message(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email on behalf of the authenticated user.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.

    Returns:
        The Gmail API send response dict (contains the new message ID).
    """
    service = _gmail_service()
    mime_message = MIMEText(body)
    mime_message["to"] = to
    mime_message["subject"] = subject

    raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
    message = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"id": message["id"], "status": "sent"}
