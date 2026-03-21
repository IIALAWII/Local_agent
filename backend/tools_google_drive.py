"""Google Drive tool for the LangChain agent.

Provides file listing, download, and upload capabilities via the Drive API v3.
"""

from __future__ import annotations

import io
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from tools_google_auth import get_google_credentials


def _drive_service() -> Any:
    """Build and return an authenticated Google Drive API service.

    Returns:
        A :mod:`googleapiclient` resource for the Drive API v3.
    """
    creds = get_google_credentials()
    return build("drive", "v3", credentials=creds)


# ── Read helpers ──────────────────────────────────────────────────────────────


def list_files(
    max_results: int = 20,
    query: str = "",
    fields: str = "files(id, name, mimeType, size, modifiedTime)",
) -> list[dict[str, Any]]:
    """List files in the authenticated user's Google Drive.

    Args:
        max_results: Maximum number of files to return.
        query: Drive query string (e.g. ``"mimeType='application/pdf'"``).
        fields: Comma-separated fields to return for each file.

    Returns:
        List of file metadata dicts.
    """
    service = _drive_service()
    params: dict[str, Any] = {
        "pageSize": max_results,
        "fields": f"nextPageToken, {fields}",
    }
    if query:
        params["q"] = query

    result = service.files().list(**params).execute()
    return result.get("files", [])


def get_file_metadata(file_id: str) -> dict[str, Any]:
    """Retrieve metadata for a specific Drive file.

    Args:
        file_id: The Google Drive file ID.

    Returns:
        File metadata dict with ``id``, ``name``, ``mimeType``, and ``webViewLink``.
    """
    service = _drive_service()
    return (
        service.files()
        .get(fileId=file_id, fields="id, name, mimeType, size, modifiedTime, webViewLink")
        .execute()
    )


def download_file(file_id: str) -> bytes:
    """Download a binary file from Google Drive.

    Args:
        file_id: The Google Drive file ID.

    Returns:
        Raw file bytes.
    """
    service = _drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


def export_google_doc(file_id: str, mime_type: str = "text/plain") -> bytes:
    """Export a Google Workspace document (Docs, Sheets, etc.) in the given MIME type.

    Args:
        file_id: The Google Drive file ID of the Workspace document.
        mime_type: Target export MIME type (e.g. ``"text/plain"``, ``"application/pdf"``).

    Returns:
        Exported file bytes.
    """
    service = _drive_service()
    request = service.files().export_media(fileId=file_id, mimeType=mime_type)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


# ── Write helpers ─────────────────────────────────────────────────────────────


def upload_file(
    local_path: str,
    name: str,
    mime_type: str = "application/octet-stream",
    parent_folder_id: str | None = None,
) -> dict[str, Any]:
    """Upload a local file to Google Drive.

    Args:
        local_path: Absolute path to the file on disk.
        name: Desired filename in Drive.
        mime_type: MIME type of the file being uploaded.
        parent_folder_id: Optional Drive folder ID to upload into.

    Returns:
        Dict with the uploaded file ``id`` and ``name``.
    """
    service = _drive_service()
    file_metadata: dict[str, Any] = {"name": name}
    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]

    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    created = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name")
        .execute()
    )
    return {"id": created["id"], "name": created["name"]}


def create_folder(name: str, parent_folder_id: str | None = None) -> dict[str, Any]:
    """Create a folder in Google Drive.

    Args:
        name: Folder name.
        parent_folder_id: Optional parent folder ID; places in root if omitted.

    Returns:
        Dict with the created folder ``id`` and ``name``.
    """
    service = _drive_service()
    metadata: dict[str, Any] = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]

    created = service.files().create(body=metadata, fields="id, name").execute()
    return {"id": created["id"], "name": created["name"]}
