#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "jira>=3.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
Fetch JIRA data for all team members defined in a config file.

Queries closed, open, stale, and blocked issues per team member.
Outputs flat JSON to stdout for consumption by the team-weekly-report skill.

Authentication:
  JIRA_API_TOKEN environment variable must be set with a valid API token
  JIRA_EMAIL (or JIRA_USERNAME) environment variable must be set

Usage:
  fetch_team_jira.py --config team-config.yaml
  fetch_team_jira.py --config team-config.yaml --days 14
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

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

    members = team.get("members")
    if not members:
        print("ERROR: Config missing 'team.members'.", file=sys.stderr)
        sys.exit(1)

    return config


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


def format_issue(issue: object) -> dict:
    """Extract relevant fields from a JIRA issue object."""
    fields = issue.fields
    assignee = getattr(fields, "assignee", None)
    assignee_name = assignee.displayName if assignee else ""
    priority = getattr(fields, "priority", None)
    summary = getattr(fields, "summary", "") or ""
    status = getattr(fields, "status", None)

    return {
        "key": issue.key,
        "summary": summary,
        "status": str(status) if status else "",
        "assignee": assignee_name,
        "priority": str(priority) if priority else "",
        "created": str(getattr(fields, "created", "") or ""),
        "updated": str(getattr(fields, "updated", "") or ""),
    }


def search_issues(jira: JIRA, jql: str) -> list[dict]:
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
            results.append(format_issue(issue))

        if len(batch) < batch_size:
            break
        start_at += batch_size

    return results


def fetch_member_data(
    jira: JIRA,
    member: dict,
    project: str,
    component: str | None,
    cutoff_date: str,
    stale_date: str,
) -> dict:
    """Fetch all JIRA data for one team member."""
    username = member.get("jira_username", "")
    name = member.get("name", "")

    if not username:
        return {
            "name": name,
            "error": f"No jira_username configured for '{name}'",
        }

    component_clause = f' AND component = "{component}"' if component else ""
    base = f'project = "{project}"{component_clause} AND assignee = "{username}"'

    data: dict = {
        "name": name,
        "jira_username": username,
    }

    # Closed issues in the lookback window
    closed_jql = f'{base} AND status changed to (Done, Closed) AFTER "{cutoff_date}"'
    data["closed_issues"] = search_issues(jira, closed_jql)

    # Open issues
    open_jql = f"{base} AND status NOT IN (Done, Closed)"
    data["open_issues"] = search_issues(jira, open_jql)

    # Stale issues (open + not updated recently)
    stale_jql = f'{base} AND status NOT IN (Done, Closed) AND updated < "{stale_date}"'
    data["stale_issues"] = search_issues(jira, stale_jql)

    # Blocked issues
    blocked_jql = f'{base} AND status = "Blocked"'
    data["blocked_issues"] = search_issues(jira, blocked_jql)

    return data


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
        "--days",
        type=int,
        default=None,
        help="Lookback days (overrides config default, fallback: 7)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    team = config["team"]
    jira_cfg = team["jira"]
    defaults = config.get("defaults", {})

    lookback_days = args.days or defaults.get("jira_lookback_days", 7)
    stale_days = defaults.get("stale_threshold_days", lookback_days)

    now = datetime.now(timezone.utc)
    cutoff_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    stale_date = (now - timedelta(days=stale_days)).strftime("%Y-%m-%d")

    jira = get_jira_client(jira_cfg["url"])

    project = jira_cfg["project"]
    component = jira_cfg.get("component")
    members = team["members"]

    print(
        f"Fetching JIRA data for {len(members)} team members...",
        file=sys.stderr,
    )

    member_results = []
    for member in members:
        name = member.get("name", "unknown")
        print(f"  Fetching data for {name}...", file=sys.stderr)
        try:
            data = fetch_member_data(jira, member, project, component, cutoff_date, stale_date)
        except Exception as e:
            data = {"name": name, "error": str(e)}
            print(f"  ERROR for {name}: {e}", file=sys.stderr)
        member_results.append(data)

    result = {
        "team_name": team.get("name", ""),
        "metadata": {
            "fetched_at": now.isoformat(),
            "lookback_days": lookback_days,
            "stale_threshold_days": stale_days,
            "jira_url": jira_cfg["url"],
            "project": project,
            "component": component,
        },
        "members": member_results,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
