#!/usr/bin/env python3
"""Find the transcript or notes Google Doc for a meeting.

Reads a calendar event JSON object (from find_meeting.py) on stdin.
Checks the event's attachments first, then falls back to Drive keyword searches.

Exit codes:
  0  Document found — JSON written to stdout
  1  Not found or error
"""

import argparse
import json
import subprocess
import sys

ATTACHMENT_KEYWORDS: tuple[str, ...] = ("transcript", "notes", "gemini")
DRIVE_FALLBACK_TERMS: tuple[str, ...] = ("transcript", "Notes from", "Notes by Gemini")


def run_gws(*args: str) -> dict:
    try:
        result = subprocess.run(["gws", *args], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        print(f"gws timed out after {e.timeout}s", file=sys.stderr)
        if stdout:
            print(f"stdout: {stdout.strip()}", file=sys.stderr)
        if stderr:
            print(f"stderr: {stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error running gws: {e}", file=sys.stderr)
        sys.exit(1)
    stdout = "\n".join(
        line for line in result.stdout.splitlines() if not line.startswith("Using keyring")
    ).strip()
    if result.returncode != 0:
        print(f"gws error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    if not stdout:
        print("gws returned no output", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"Failed to parse gws JSON response: {e}\nRaw output: {stdout!r}", file=sys.stderr)
        sys.exit(1)


def check_attachments(event_data: dict) -> dict | None:
    """Return attachment info if the event has a notes/transcript Google Doc."""
    # Support both a single event object and a calendar events list response.
    items: list[dict] = event_data.get("items", [event_data] if "attachments" in event_data else [])
    for item in items:
        for att in item.get("attachments", []):
            if att.get("mimeType") != "application/vnd.google-apps.document":
                continue
            file_id = att.get("fileId")
            if not file_id:
                continue
            if any(kw in att.get("title", "").lower() for kw in ATTACHMENT_KEYWORDS):
                return {
                    "source": "attachment",
                    "fileId": file_id,
                    "title": att.get("title", ""),
                }
    return None


def search_drive(term: str) -> list[dict]:
    """Search Drive for Google Docs whose name contains *term*."""
    escaped = term.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
    params = {
        "q": (
            f"name contains '{escaped}'"
            " and mimeType = 'application/vnd.google-apps.document'"
            " and trashed = false"
        ),
        "orderBy": "createdTime desc",
        "pageSize": 10,
        "fields": "files(id,name,mimeType,createdTime,webViewLink)",
    }
    data = run_gws("drive", "files", "list", "--params", json.dumps(params))
    return data.get("files", [])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    try:
        raw_stdin = sys.stdin.read()
        event_data = json.loads(raw_stdin)
    except json.JSONDecodeError as e:
        print(f"Failed to parse stdin as JSON: {e}\nRaw input: {raw_stdin!r}", file=sys.stderr)
        sys.exit(1)

    # 2a: Check calendar event attachments first.
    result = check_attachments(event_data)
    if result:
        print(json.dumps(result, indent=2))
        return

    # 2b: Fall back to Drive searches.
    # Extract event title to use as the first search term.
    items: list[dict] = event_data.get("items", [event_data])
    if not items:
        print(json.dumps({"source": "none", "files": []}, indent=2))
        sys.exit(1)

    event_title: str = items[0].get("summary", "")
    search_terms: list[str] = ([event_title] if event_title else []) + list(DRIVE_FALLBACK_TERMS)

    for term in search_terms:
        files = search_drive(term)
        if files:
            print(json.dumps({"source": "drive", "files": files}, indent=2))
            return

    print(json.dumps({"source": "none", "files": []}, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    main()
