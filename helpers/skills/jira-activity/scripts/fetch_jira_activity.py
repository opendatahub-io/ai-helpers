#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "jira>=3.0.0",
# ]
# ///
"""
Fetch activity data for a Jira ticket and its entire descendant hierarchy.

Recursively collects status, assignee, comments, and changelog entries for
a target ticket and all its descendants (Initiative → Epic → Stories/Tasks).
Discovers relationships via subtasks, "is parent of" links, and reverse
relationships ("Parent Link", "Epic Link"). Filters out bot activity and
noisy changelog fields. Outputs flat JSON hierarchy to stdout.

Authentication:
  JIRA_API_TOKEN environment variable must be set with a valid API token

Usage:
  fetch_jira_activity.py <ticket-key> [--days N]

Examples:
  fetch_jira_activity.py RHOAIENG-1234
  fetch_jira_activity.py RHOAIENG-1234 --days 60
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

from jira import JIRA
from jira.exceptions import JIRAError

JIRA_URL = "https://issues.redhat.com"

BOT_PATTERNS = ["[bot]", "automation", "jira-bot", "serviceaccount", "addon_"]

MAX_COMMENT_LENGTH = 300


def get_jira_client() -> JIRA:
    """Create an authenticated JIRA client."""
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print(
            "ERROR: JIRA_API_TOKEN environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)
    return JIRA(server=JIRA_URL, token_auth=token)


def is_bot(display_name: str) -> bool:
    """Check if a display name matches known bot patterns."""
    name_lower = display_name.lower()
    return any(pattern in name_lower for pattern in BOT_PATTERNS)


def parse_jira_datetime(dt_str: str) -> datetime:
    """Parse a Jira datetime string into a timezone-aware datetime."""
    # Normalize trailing "Z" to "+00:00" (required for Python <3.11)
    if dt_str and dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    # Jira returns ISO 8601 with timezone offset like 2025-01-15T10:30:00.000+0000
    # Replace the +0000 style offset with +00:00 for fromisoformat
    if dt_str and len(dt_str) >= 5 and dt_str[-5] in ("+", "-") and ":" not in dt_str[-5:]:
        dt_str = dt_str[:-2] + ":" + dt_str[-2:]
    dt = datetime.fromisoformat(dt_str)
    # Ensure timezone-aware so comparisons with cutoff don't raise TypeError
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def collect_issue_data(jira: JIRA, key: str, cutoff: datetime) -> tuple[dict, object]:
    """Collect activity data for a single issue. Returns (data_dict, issue_object)."""
    issue = jira.issue(key, expand="changelog")
    fields = issue.fields

    assignee_name = ""
    if fields.assignee:
        assignee_name = fields.assignee.displayName

    data: dict = {
        "key": issue.key,
        "summary": fields.summary,
        "status": str(fields.status),
        "assignee": assignee_name,
        "updated": str(fields.updated),
        "comments": [],
        "changelog": [],
    }

    # Collect recent human comments
    comments = getattr(fields, "comment", None)
    for comment in comments.comments if comments else []:
        created = parse_jira_datetime(comment.created)
        if created < cutoff:
            continue
        author_name = comment.author.displayName if comment.author else "Unknown"
        if is_bot(author_name):
            continue
        body = comment.body
        if len(body) > MAX_COMMENT_LENGTH:
            body = body[:MAX_COMMENT_LENGTH] + "..."
        data["comments"].append(
            {
                "author": author_name,
                "created": comment.created,
                "body": body,
            }
        )

    # Collect recent changelog entries (status/assignee changes only)
    for history in issue.changelog.histories:
        created = parse_jira_datetime(history.created)
        if created < cutoff:
            continue
        author_name = history.author.displayName if history.author else "Unknown"
        if is_bot(author_name):
            continue
        for item in history.items:
            field_lower = item.field.lower()
            if field_lower not in ("status", "assignee"):
                continue
            data["changelog"].append(
                {
                    "author": author_name,
                    "created": history.created,
                    "field": item.field,
                    "from": item.fromString,
                    "to": item.toString,
                }
            )

    return data, issue


def find_child_keys(jira: JIRA, issue, key: str) -> list[str]:
    """Find child issue keys from subtasks, 'is parent of' links, and reverse relationships."""
    children: list[str] = []

    # Subtasks
    if issue.fields.subtasks:
        for subtask in issue.fields.subtasks:
            children.append(subtask.key)

    # Issue links where this issue "is parent of" another
    if issue.fields.issuelinks:
        for link in issue.fields.issuelinks:
            if hasattr(link, "outwardIssue") and link.type.outward == "is parent of":
                children.append(link.outwardIssue.key)

    # Search for issues that link TO this issue (reverse relationships)
    reverse_link_fields = [
        '"Parent Link"',  # Red Hat Jira Initiative -> Epic
        '"Epic Link"',  # Standard Epic -> Story/Task
    ]

    batch_size = 100
    for field in reverse_link_fields:
        try:
            jql = f"{field} = {key}"
            start_at = 0
            while True:
                batch = jira.search_issues(jql, startAt=start_at, maxResults=batch_size)
                for linked_issue in batch:
                    children.append(linked_issue.key)
                if len(batch) < batch_size:
                    break
                start_at += batch_size
        except JIRAError:
            # Field doesn't exist or no permission for this link type
            continue

    return list(set(children))  # Remove duplicates


def collect_hierarchy_data(
    jira: JIRA,
    key: str,
    cutoff: datetime,
    level: int = 0,
    parent_key: str = None,
    visited: set = None,
) -> list[dict]:
    """Recursively collect data for an issue and all its descendants."""
    if visited is None:
        visited = set()

    # Avoid infinite loops
    if key in visited:
        return []
    visited.add(key)

    issues = []

    try:
        # Collect data for this issue
        issue_data, issue_obj = collect_issue_data(jira, key, cutoff)
        issue_data["level"] = level
        issue_data["parent_key"] = parent_key
        issues.append(issue_data)

        # Recursively collect children
        child_keys = find_child_keys(jira, issue_obj, key)
        for child_key in child_keys:
            child_issues = collect_hierarchy_data(jira, child_key, cutoff, level + 1, key, visited)
            issues.extend(child_issues)

    except Exception as e:
        # Add error entry for failed issues
        issues.append({"key": key, "level": level, "parent_key": parent_key, "error": str(e)})

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "ticket_key",
        help="JIRA ticket key (e.g., RHOAIENG-1234)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back for activity (default: 30)",
    )
    args = parser.parse_args()

    cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff = cutoff - timedelta(days=args.days)

    jira = get_jira_client()

    # Recursively collect the entire hierarchy
    try:
        all_issues = collect_hierarchy_data(jira, args.ticket_key, cutoff)
    except Exception as e:
        print(
            f"ERROR: Unable to fetch hierarchy for {args.ticket_key}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    result = {
        "issues": all_issues,
        "metadata": {
            "root_issue": args.ticket_key,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "lookback_days": args.days,
            "cutoff_date": cutoff.isoformat(),
            "jira_url": JIRA_URL,
            "total_issues": len(all_issues),
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
