#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "jira>=3.0.0",
# ]
# ///
"""
Fetch sprint planning data from AIPCC Jira project for Ecosystems squads.

Queries all Features, Initiatives, Epics, and Stories for a specified fix version,
groups them by squad using custom field team assignments, and outputs structured
JSON for sprint planning analysis.

Authentication:
  JIRA_API_TOKEN environment variable must be set with a valid API token
  JIRA_EMAIL environment variable must be set with your Atlassian account email

Configuration:
  Reads ~/.claude/sprint-planning-config.json for team mappings and project settings

Usage:
  fetch_sprint_data.py --fix-version <version> [--config <path>]

Examples:
  fetch_sprint_data.py --fix-version rhoai-3.5.EA2
  fetch_sprint_data.py --fix-version rhoai-3.5.EA3 --config ~/custom-config.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from jira import JIRA
from jira.exceptions import JIRAError

JIRA_URL = "https://redhat.atlassian.net"
DEFAULT_CONFIG_PATH = Path.home() / ".claude" / "sprint-planning-config.json"
TEAM_FIELD_ID = "customfield_10001"  # Team assignment custom field


def get_jira_client() -> JIRA:
    """Create an authenticated JIRA client."""
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print(
            "ERROR: JIRA_API_TOKEN environment variable is not set.",
            file=sys.stderr,
        )
        print("Set it with: export JIRA_API_TOKEN='your-token-here'", file=sys.stderr)
        sys.exit(1)
    email = os.environ.get("JIRA_EMAIL")
    if not email:
        print(
            "ERROR: JIRA_EMAIL environment variable is not set.",
            file=sys.stderr,
        )
        print("Set it with: export JIRA_EMAIL='your-email@redhat.com'", file=sys.stderr)
        sys.exit(1)
    return JIRA(server=JIRA_URL, basic_auth=(email, token))


def load_config(config_path: Path) -> dict:
    """Load configuration file with team mappings and project settings."""
    if not config_path.exists():
        print(
            f"ERROR: Configuration file not found: {config_path}",
            file=sys.stderr,
        )
        print(
            "Create it with team_mapping, jira_project, and components settings.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Invalid JSON in configuration file: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate required fields
    required = ["team_mapping", "jira_project", "components"]
    missing = [field for field in required if field not in config]
    if missing:
        print(
            f"ERROR: Configuration missing required fields: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    return config


def fetch_issues(jira: JIRA, project: str, fix_version: str, components: list[str]) -> list[dict]:
    """Fetch all issues for the fix version and components."""
    # Build component filter
    component_filter = " OR ".join([f'component = "{comp}"' for comp in components])

    # JQL query for all issue types in the fix version
    jql = f'project = {project} AND fixVersion = "{fix_version}" AND ({component_filter})'

    print(f"Querying Jira: {jql}", file=sys.stderr)

    issues = []
    batch_size = 100
    start_at = 0

    try:
        while True:
            batch = jira.search_issues(
                jql,
                startAt=start_at,
                maxResults=batch_size,
                fields="summary,status,assignee,issuetype,parent,customfield_10001,components,fixVersions",
            )

            for issue in batch:
                fields = issue.fields

                # Get team assignment from custom field
                team_id = None
                team_field = getattr(fields, TEAM_FIELD_ID, None)
                if team_field and hasattr(team_field, "id"):
                    team_id = team_field.id

                # Get parent key if exists
                parent_key = None
                if hasattr(fields, "parent") and fields.parent:
                    parent_key = fields.parent.key

                # Get assignee
                assignee = ""
                if fields.assignee:
                    assignee = fields.assignee.displayName

                # Get components
                components_list = (
                    [comp.name for comp in fields.components] if fields.components else []
                )

                issue_data = {
                    "key": issue.key,
                    "summary": fields.summary,
                    "status": str(fields.status),
                    "issue_type": str(fields.issuetype),
                    "assignee": assignee,
                    "team_id": team_id,
                    "parent_key": parent_key,
                    "components": components_list,
                    "url": f"{JIRA_URL}/browse/{issue.key}",
                }

                issues.append(issue_data)

            print(f"Fetched {len(issues)} issues so far...", file=sys.stderr)

            if len(batch) < batch_size:
                break
            start_at += batch_size

    except JIRAError as e:
        print(
            f"ERROR: Failed to fetch issues: {e.text if hasattr(e, 'text') else str(e)}",
            file=sys.stderr,
        )
        sys.exit(1)

    return issues


def group_by_squad(issues: list[dict], team_mapping: dict) -> dict:
    """Group issues by squad using team mapping."""
    squads = {squad_name: [] for squad_name in team_mapping.values()}
    squads["Unassigned"] = []

    for issue in issues:
        team_id = issue.get("team_id")

        if team_id and team_id in team_mapping:
            squad_name = team_mapping[team_id]
            squads[squad_name].append(issue)
        else:
            squads["Unassigned"].append(issue)

    return squads


def analyze_squad_data(squad_issues: list[dict]) -> dict:
    """Analyze issues for a squad and compute metrics."""
    # Group by issue type
    by_type = {}
    for issue in squad_issues:
        issue_type = issue["issue_type"]
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)

    # Group by status
    by_status = {}
    for issue in squad_issues:
        status = issue["status"]
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(issue)

    # Epic-specific analysis (only count Epics)
    epics = [i for i in squad_issues if i["issue_type"] == "Epic"]
    epic_statuses = {}
    for epic in epics:
        status = epic["status"]
        epic_statuses[status] = epic_statuses.get(status, 0) + 1

    # Get parent features for epics
    parent_features = set()
    for epic in epics:
        if epic.get("parent_key"):
            parent_features.add(epic["parent_key"])

    return {
        "total_issues": len(squad_issues),
        "total_epics": len(epics),
        "by_type": {itype: len(items) for itype, items in by_type.items()},
        "by_status": {status: len(items) for status, items in by_status.items()},
        "epic_statuses": epic_statuses,
        "parent_features": list(parent_features),
        "epics": epics,
        "all_issues": squad_issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--fix-version",
        required=True,
        help="Fix version to query (e.g., rhoai-3.5.EA2)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file (default: {DEFAULT_CONFIG_PATH})",
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    team_mapping = config["team_mapping"]
    project = config["jira_project"]
    components = config["components"]

    # Create Jira client
    jira = get_jira_client()

    # Fetch all issues
    print(f"Fetching issues for fix version: {args.fix_version}", file=sys.stderr)
    issues = fetch_issues(jira, project, args.fix_version, components)

    print(f"Total issues fetched: {len(issues)}", file=sys.stderr)

    # Group by squad
    squads = group_by_squad(issues, team_mapping)

    # Analyze each squad
    squad_analysis = {}
    for squad_name, squad_issues in squads.items():
        if squad_issues:  # Only include squads with work
            squad_analysis[squad_name] = analyze_squad_data(squad_issues)

    # Build result
    result = {
        "fix_version": args.fix_version,
        "project": project,
        "squads": squad_analysis,
        "metadata": {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "total_issues": len(issues),
            "total_epics": sum(
                len([i for i in squad_issues if i["issue_type"] == "Epic"])
                for squad_issues in squads.values()
            ),
            "jira_url": JIRA_URL,
        },
    }

    # Output JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
