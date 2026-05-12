#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "jira>=3.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
Fetch JIRA data for a single engineer from the team config.

Queries active issues (with created date for days-open calculation) and
blocked issues. Outputs JSON to stdout for the engineer-snapshot skill.

Authentication:
  JIRA_API_TOKEN environment variable must be set with a valid API token
  JIRA_EMAIL (or JIRA_USERNAME) environment variable must be set

Usage:
  fetch_engineer_jira.py --config team-config.yaml --engineer "Engineer One"
  fetch_engineer_jira.py --config team-config.yaml --engineer "Engineer One" --days 14
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import yaml
from jira import JIRA
from jira.exceptions import JIRAError


def load_config(path: str) -> dict:
    """Load and validate team config YAML."""
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    team = config.get("team")
    if not team:
        print("ERROR: Config missing 'team' key.", file=sys.stderr)
        sys.exit(1)

    jira_cfg = team.get("jira")
    if not jira_cfg or not jira_cfg.get("url") or not jira_cfg.get("project"):
        print(
            "ERROR: Config missing 'team.jira.url' or 'team.jira.project'.",
            file=sys.stderr,
        )
        sys.exit(1)

    return config


def find_member(config: dict, engineer_name: str) -> dict | None:
    """Find a team member by name (case-insensitive)."""
    members = config.get("team", {}).get("members", [])
    name_lower = engineer_name.lower()
    for member in members:
        if member.get("name", "").lower() == name_lower:
            return member
    # Partial match fallback
    for member in members:
        if name_lower in member.get("name", "").lower():
            return member
    return None


def get_jira_client(url: str) -> JIRA:
    """Create an authenticated JIRA client."""
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print(
            "ERROR: JIRA_API_TOKEN environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)
    email = os.environ.get("JIRA_EMAIL") or os.environ.get("JIRA_USERNAME")
    if not email:
        print(
            "ERROR: JIRA_EMAIL (or JIRA_USERNAME) environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)
    return JIRA(server=url, basic_auth=(email, token), timeout=30)


def _parse_jira_datetime(dt_str: str) -> datetime | None:
    """Parse a Jira datetime string into a timezone-aware datetime."""
    if not dt_str:
        return None
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        if len(dt_str) >= 5 and dt_str[-5] in ("+", "-") and ":" not in dt_str[-5:]:
            dt_str = dt_str[:-2] + ":" + dt_str[-2:]
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def format_issue(issue: object, now: datetime) -> dict:
    """Extract relevant fields from a JIRA issue and compute days open."""
    fields = issue.fields
    assignee = getattr(fields, "assignee", None)
    assignee_name = assignee.displayName if assignee else ""

    created_str = str(getattr(fields, "created", "") or "")
    updated_str = str(getattr(fields, "updated", "") or "")
    priority = getattr(fields, "priority", None)
    summary = getattr(fields, "summary", "") or ""
    status = getattr(fields, "status", None)

    days_open = None
    created_dt = _parse_jira_datetime(created_str)
    if created_dt:
        days_open = (now - created_dt).days

    return {
        "key": issue.key,
        "summary": summary,
        "status": str(status) if status else "",
        "assignee": assignee_name,
        "priority": str(priority) if priority else "",
        "created": created_str,
        "updated": updated_str,
        "days_open": days_open,
    }


def search_issues(jira: JIRA, jql: str, now: datetime) -> list[dict]:
    """Run a JQL query and return formatted issues."""
    results = []
    start_at = 0
    batch_size = 100
    while True:
        try:
            batch = jira.search_issues(
                jql,
                startAt=start_at,
                maxResults=batch_size,
            )
        except JIRAError as e:
            print(f"WARNING: JQL query failed: {e.text}", file=sys.stderr)
            return results

        for issue in batch:
            results.append(format_issue(issue, now))

        if len(batch) < batch_size:
            break
        start_at += batch_size

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to team config YAML file",
    )
    parser.add_argument(
        "--engineer",
        required=True,
        help="Engineer display name (e.g., 'Engineer One')",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Lookback days for stale threshold (overrides config, fallback: 7)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    member = find_member(config, args.engineer)

    if not member:
        available = [m.get("name", "?") for m in config.get("team", {}).get("members", [])]
        print(
            f"ERROR: Engineer '{args.engineer}' not found in config. "
            f"Available members: {', '.join(available)}",
            file=sys.stderr,
        )
        sys.exit(1)

    team = config["team"]
    jira_cfg = team["jira"]
    username = member.get("jira_username", "")

    if not username:
        print(
            f"ERROR: No jira_username configured for '{member['name']}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    jira = get_jira_client(jira_cfg["url"])
    now = datetime.now(timezone.utc)

    project = jira_cfg["project"]
    component = jira_cfg.get("component")
    component_clause = f' AND component = "{component}"' if component else ""
    base = f'project = "{project}"{component_clause} AND assignee = "{username}"'

    print(f"Fetching JIRA data for {member['name']}...", file=sys.stderr)

    # Active issues (not done/closed)
    active_jql = f"{base} AND status NOT IN (Done, Closed)"
    active_issues = search_issues(jira, active_jql, now)

    # Blocked issues
    blocked_jql = f'{base} AND status = "Blocked"'
    blocked_issues = search_issues(jira, blocked_jql, now)

    result = {
        "engineer": {
            "name": member["name"],
            "jira_username": username,
            "github_username": member.get("github_username", ""),
            "notes_file": member.get("notes_file", ""),
        },
        "metadata": {
            "fetched_at": now.isoformat(),
            "jira_url": jira_cfg["url"],
            "project": project,
            "component": component,
        },
        "active_issues": active_issues,
        "blocked_issues": blocked_issues,
        "summary": {
            "active_count": len(active_issues),
            "blocked_count": len(blocked_issues),
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
