"""Google Calendar tool for the LangChain agent.

Provides event listing and creation capabilities via the Google Calendar API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from googleapiclient.discovery import build

from tools_google_auth import get_google_credentials


def _calendar_service() -> Any:
    """Build and return an authenticated Google Calendar API service.

    Returns:
        A :mod:`googleapiclient` resource for the Calendar API v3.
    """
    creds = get_google_credentials()
    return build("calendar", "v3", credentials=creds)


# ── Read helpers ──────────────────────────────────────────────────────────────


def list_events(
    calendar_id: str = "primary",
    max_results: int = 10,
    time_min: str | None = None,
    time_max: str | None = None,
) -> list[dict[str, Any]]:
    """List upcoming calendar events.

    Args:
        calendar_id: Calendar ID to query; defaults to the user's primary calendar.
        max_results: Maximum number of events to return.
        time_min: Lower bound (RFC 3339 timestamp) for event start time.
        time_max: Upper bound (RFC 3339 timestamp) for event start time.

    Returns:
        List of simplified event dicts with ``id``, ``summary``, ``start``,
        ``end``, and ``description`` fields.
    """
    service = _calendar_service()
    now = datetime.now(timezone.utc).isoformat()

    params: dict[str, Any] = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
        "timeMin": time_min or now,
    }
    if time_max:
        params["timeMax"] = time_max

    result = service.events().list(**params).execute()
    events = result.get("items", [])

    return [
        {
            "id": e.get("id"),
            "summary": e.get("summary", "(No title)"),
            "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
            "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
            "description": e.get("description", ""),
            "location": e.get("location", ""),
        }
        for e in events
    ]


def get_event(event_id: str, calendar_id: str = "primary") -> dict[str, Any]:
    """Fetch a single calendar event by its ID.

    Args:
        event_id: The Google Calendar event ID.
        calendar_id: The calendar the event belongs to.

    Returns:
        Simplified event dict.
    """
    service = _calendar_service()
    e = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    return {
        "id": e.get("id"),
        "summary": e.get("summary", "(No title)"),
        "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
        "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
        "description": e.get("description", ""),
        "location": e.get("location", ""),
        "attendees": [a.get("email") for a in e.get("attendees", [])],
    }


# ── Write helpers ─────────────────────────────────────────────────────────────


def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    attendees: list[str] | None = None,
    calendar_id: str = "primary",
) -> dict[str, Any]:
    """Create a new calendar event.

    Args:
        summary: Event title.
        start_datetime: RFC 3339 start datetime string (e.g. ``"2025-01-15T10:00:00Z"``).
        end_datetime: RFC 3339 end datetime string.
        description: Optional event description.
        location: Optional event location.
        attendees: Optional list of attendee email addresses.
        calendar_id: Calendar to add the event to.

    Returns:
        Dict with the created event ``id`` and ``htmlLink``.
    """
    service = _calendar_service()

    event_body: dict[str, Any] = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start_datetime, "timeZone": "UTC"},
        "end": {"dateTime": end_datetime, "timeZone": "UTC"},
    }
    if attendees:
        event_body["attendees"] = [{"email": e} for e in attendees]

    created = (
        service.events()
        .insert(calendarId=calendar_id, body=event_body)
        .execute()
    )
    return {"id": created["id"], "htmlLink": created.get("htmlLink", "")}


def delete_event(event_id: str, calendar_id: str = "primary") -> dict[str, str]:
    """Delete a calendar event.

    Args:
        event_id: The ID of the event to delete.
        calendar_id: The calendar the event belongs to.

    Returns:
        Dict with a ``status`` field set to ``"deleted"``.
    """
    service = _calendar_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return {"status": "deleted", "event_id": event_id}
