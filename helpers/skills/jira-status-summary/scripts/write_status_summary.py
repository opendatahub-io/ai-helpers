#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "requests>=2.28.0",
# ]
# ///
"""
Write a formatted Status Summary to a Jira ticket's custom field.

Builds a date-stamped status string with health color and AI disclaimer,
converts it to Atlassian Document Format (ADF), and writes it to the
"Status Summary" custom field via the Jira REST API v3.

Authentication:
  JIRA_API_TOKEN environment variable must be set with a valid API token
  JIRA_EMAIL (or JIRA_USER) environment variable must be set

Usage:
  write_status_summary.py <ticket-key> --color green --summary "Summary text."
  write_status_summary.py <ticket-key> --color green --summary "Summary text." --dry-run

Examples:
  write_status_summary.py AIPCC-12345 --color green --summary "On track. Two epics completed."
  write_status_summary.py AIPCC-12345 --color yellow --summary "Some delays on Epic X."
  write_status_summary.py AIPCC-12345 --color red --summary "Blocked on dependency Y."
  write_status_summary.py AIPCC-12345 --color green --summary "On track." --dry-run
"""

import argparse
import os
import sys
from datetime import datetime, timezone

import requests

JIRA_URL = "https://redhat.atlassian.net"
API_VERSION = "3"
API_TIMEOUT = int(os.getenv("JIRA_API_TIMEOUT", "30"))
STATUS_FIELD_NAME = "Status Summary"

COLOR_MAP = {
    "green": ("Green", "\U0001f7e2"),
    "yellow": ("Yellow", "\U0001f7e1"),
    "red": ("Red", "\U0001f534"),
}


def api_url(path: str) -> str:
    return f"{JIRA_URL}/rest/api/{API_VERSION}/{path}"


def get_auth() -> tuple[str, str]:
    email = os.getenv("JIRA_EMAIL") or os.getenv("JIRA_USER")
    token = os.getenv("JIRA_API_TOKEN")
    if not email:
        print("ERROR: JIRA_EMAIL (or JIRA_USER) environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    if not token:
        print("ERROR: JIRA_API_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return (email, token)


def build_status_text(color: str, summary: str) -> str:
    color_label, emoji = COLOR_MAP[color]
    date_str = datetime.now(timezone.utc).strftime("%d/%b/%Y")
    return (
        f"{date_str} {color_label} {emoji}\n"
        f"\u26a0\ufe0f AI-generated summary \u2014 please review before the Program Call.\n"
        f"\n"
        f"{summary}"
    )


def text_to_adf(text: str) -> dict:
    paragraphs = []
    for line in text.split("\n"):
        if line.strip():
            paragraphs.append({"type": "paragraph", "content": [{"type": "text", "text": line}]})
        else:
            paragraphs.append({"type": "paragraph", "content": []})
    return {"version": 1, "type": "doc", "content": paragraphs}


def find_field_id(field_name: str, auth: tuple[str, str]) -> str:
    resp = requests.get(
        api_url("field"),
        headers={"Content-Type": "application/json"},
        auth=auth,
        timeout=API_TIMEOUT,
    )
    if resp.status_code != 200:
        print(f"ERROR: HTTP {resp.status_code} fetching fields: {resp.text}", file=sys.stderr)
        sys.exit(1)
    for field in resp.json():
        if field.get("name") == field_name:
            return field["id"]
    print(f"ERROR: Field '{field_name}' not found in Jira metadata.", file=sys.stderr)
    sys.exit(1)


def write_field(ticket: str, field_id: str, adf_value: dict, auth: tuple[str, str]) -> None:
    resp = requests.put(
        api_url(f"issue/{ticket}"),
        headers={"Content-Type": "application/json"},
        json={"fields": {field_id: adf_value}},
        auth=auth,
        timeout=API_TIMEOUT,
    )
    if resp.status_code == 204:
        print(f"Updated '{STATUS_FIELD_NAME}' on {ticket}")
    else:
        print(f"ERROR: HTTP {resp.status_code} updating {ticket}: {resp.text}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("ticket_key", help="Jira ticket key (e.g. AIPCC-12345)")
    parser.add_argument(
        "--color",
        required=True,
        choices=["green", "yellow", "red"],
        help="Health color: green, yellow, or red",
    )
    parser.add_argument(
        "--summary",
        required=True,
        help="AI-generated summary text (2-4 sentences)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the formatted status text without writing to Jira",
    )
    args = parser.parse_args()

    status_text = build_status_text(args.color, args.summary)

    if args.dry_run:
        print("[DRY RUN] Would write to", args.ticket_key)
        print()
        print(status_text)
        return

    auth = get_auth()
    adf_value = text_to_adf(status_text)
    field_id = find_field_id(STATUS_FIELD_NAME, auth)
    write_field(args.ticket_key, field_id, adf_value, auth)


if __name__ == "__main__":
    main()
