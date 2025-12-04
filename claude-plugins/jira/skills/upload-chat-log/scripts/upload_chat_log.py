#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "jira>=3.0.0",
# ]
# ///
"""
Upload a chat log file as an attachment to a JIRA ticket.

This script uploads a markdown file (or any file) as an attachment to a
specified JIRA ticket on https://issues.redhat.com.

Authentication:
  JIRA_API_TOKEN environment variable must be set with a valid API token

Usage:
  upload_chat_log.py <ticket-key> <file-path>

Examples:
  upload_chat_log.py AIPCC-7354 /tmp/chat-log-2025-01-20.md
  JIRA_API_TOKEN=xyz123 upload_chat_log.py PROJ-123 ./conversation.md
"""

import argparse
import os
import sys
from pathlib import Path

from jira import JIRA


def get_jira_token() -> str:
    """Get JIRA API token from environment variable."""
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print(
            "ERROR: JIRA_API_TOKEN environment variable is not set.",
            file=sys.stderr,
        )
        print(
            "\nTo obtain a JIRA API token:",
            file=sys.stderr,
        )
        print(
            "1. Go to https://issues.redhat.com",
            file=sys.stderr,
        )
        print(
            "2. Click your profile icon > Account Settings > Security",
            file=sys.stderr,
        )
        print(
            "3. Create and copy an API token",
            file=sys.stderr,
        )
        print(
            "4. Set the environment variable: export JIRA_API_TOKEN='your-token'",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def validate_file(file_path: str) -> Path:
    """Validate that the file exists and is readable."""
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File does not exist: {file_path}", file=sys.stderr)
        sys.exit(1)
    if not path.is_file():
        print(f"ERROR: Path is not a file: {file_path}", file=sys.stderr)
        sys.exit(1)
    if not os.access(path, os.R_OK):
        print(f"ERROR: File is not readable: {file_path}", file=sys.stderr)
        sys.exit(1)
    return path


def upload_attachment(ticket_key: str, file_path: Path) -> None:
    """Upload a file as an attachment to a JIRA ticket."""
    jira_url = "https://issues.redhat.com"
    token = get_jira_token()

    try:
        # Connect to JIRA using API token
        jira = JIRA(server=jira_url, token_auth=token)

        # Verify the ticket exists and is accessible
        try:
            issue = jira.issue(ticket_key)
            print(f"Found ticket: {issue.key} - {issue.fields.summary}")
        except Exception as e:
            print(
                f"ERROR: Unable to access ticket {ticket_key}: {e}",
                file=sys.stderr,
            )
            print(
                "\nPossible reasons:",
                file=sys.stderr,
            )
            print(
                "  - Ticket does not exist",
                file=sys.stderr,
            )
            print(
                "  - You don't have permission to view this ticket",
                file=sys.stderr,
            )
            print(
                "  - Invalid API token",
                file=sys.stderr,
            )
            sys.exit(1)

        # Upload the file as an attachment
        print(f"Uploading {file_path.name} to {ticket_key}...")
        with open(file_path, "rb") as f:
            attachment = jira.add_attachment(issue=ticket_key, attachment=f)

        print(f"\n✓ Successfully uploaded attachment to {ticket_key}")
        print(f"  Attachment: {attachment.filename}")
        print(f"  Size: {attachment.size} bytes")
        print(f"  View ticket: {jira_url}/browse/{ticket_key}")

    except Exception as e:
        print(f"ERROR: Failed to upload attachment: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "ticket_key",
        help="JIRA ticket key (e.g., AIPCC-1234, PROJ-567)",
    )
    parser.add_argument(
        "file_path",
        help="Path to the file to upload as an attachment",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Validate inputs
    file_path = validate_file(args.file_path)

    # Upload the attachment
    upload_attachment(args.ticket_key, file_path)


if __name__ == "__main__":
    main()
