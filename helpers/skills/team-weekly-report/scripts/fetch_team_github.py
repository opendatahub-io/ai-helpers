#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
Fetch GitHub PR data for all team members using the gh CLI.

Queries open and recently merged PRs per team member across configured
repositories. Outputs flat JSON to stdout for the team-weekly-report skill.

Prerequisites:
  gh CLI must be installed and authenticated (gh auth login)

Usage:
  fetch_team_github.py --config team-config.yaml
  fetch_team_github.py --config team-config.yaml --days 14
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import yaml

GH_SEARCH_FIELDS = "number,title,url,createdAt,updatedAt,labels"
GH_PR_LIST_FIELDS = "number,title,url,createdAt,mergedAt,labels"
GH_TIMEOUT = 30
GH_DELAY = 0.5


def load_config(path: str) -> dict:
    """Load and validate team config YAML."""
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    team = config.get("team")
    if not team:
        print("ERROR: Config missing 'team' key.", file=sys.stderr)
        sys.exit(1)

    github_cfg = team.get("github")
    if not github_cfg or not github_cfg.get("repositories"):
        print(
            "ERROR: Config missing 'team.github.repositories'.",
            file=sys.stderr,
        )
        sys.exit(1)

    members = team.get("members")
    if not members:
        print("ERROR: Config missing 'team.members'.", file=sys.stderr)
        sys.exit(1)

    return config


def check_gh_auth() -> None:
    """Verify gh CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT,
        )
        if result.returncode != 0:
            print(
                "ERROR: gh CLI is not authenticated. Run: gh auth login",
                file=sys.stderr,
            )
            sys.exit(1)
    except FileNotFoundError:
        print(
            "ERROR: gh CLI is not installed. Install from: https://cli.github.com/",
            file=sys.stderr,
        )
        sys.exit(1)


def run_gh_command(args: list[str]) -> list[dict]:
    """Run a gh CLI command and return parsed JSON."""
    cmd = ["gh", *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"WARNING: gh command timed out: {' '.join(cmd)}", file=sys.stderr)
        return []

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "no results" not in stderr.lower():
            print(
                f"WARNING: gh command failed: {stderr}",
                file=sys.stderr,
            )
        return []

    if not result.stdout.strip():
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(
            f"WARNING: Could not parse gh output as JSON: {result.stdout[:200]}",
            file=sys.stderr,
        )
        return []


def fetch_member_prs(
    username: str,
    repos: list[str],
    cutoff_date: str,
) -> dict:
    """Fetch open and merged PRs for one team member."""
    open_prs: list[dict] = []
    merged_prs: list[dict] = []

    for repo in repos:
        # Open PRs (gh search prs supports cross-repo search)
        results = run_gh_command(
            [
                "search",
                "prs",
                f"--author={username}",
                f"--repo={repo}",
                "--state=open",
                f"--json={GH_SEARCH_FIELDS}",
                "--limit=100",
            ]
        )
        for pr in results:
            pr["repo"] = repo
            pr["author"] = username
        open_prs.extend(results)
        time.sleep(GH_DELAY)

        # Merged PRs within lookback window (gh pr list supports mergedAt)
        results = run_gh_command(
            [
                "pr",
                "list",
                f"-R={repo}",
                f"-A={username}",
                "--state=merged",
                f"--json={GH_PR_LIST_FIELDS}",
                "--limit=100",
                f"-S=merged:>={cutoff_date}",
            ]
        )
        for pr in results:
            pr["repo"] = repo
            pr["author"] = username
        merged_prs.extend(results)
        time.sleep(GH_DELAY)

    return {
        "open_prs": open_prs,
        "merged_prs": merged_prs,
    }


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
        help="Lookback days for merged PRs (overrides config, fallback: 7)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    team = config["team"]
    defaults = config.get("defaults", {})

    lookback_days = args.days or defaults.get("github_lookback_days", 7)
    repos = team["github"]["repositories"]
    members = team["members"]

    check_gh_auth()

    now = datetime.now(timezone.utc)
    cutoff_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    print(
        f"Fetching GitHub PRs for {len(members)} members across {len(repos)} repos...",
        file=sys.stderr,
    )

    member_results = []
    for member in members:
        name = member.get("name", "unknown")
        github_username = member.get("github_username")

        if not github_username:
            member_results.append(
                {
                    "name": name,
                    "error": f"No github_username configured for '{name}'",
                }
            )
            continue

        print(f"  Fetching PRs for {name} ({github_username})...", file=sys.stderr)
        try:
            pr_data = fetch_member_prs(github_username, repos, cutoff_date)
            member_results.append(
                {
                    "name": name,
                    "github_username": github_username,
                    **pr_data,
                }
            )
        except Exception as e:
            member_results.append(
                {
                    "name": name,
                    "github_username": github_username,
                    "error": str(e),
                }
            )
            print(f"  ERROR for {name}: {e}", file=sys.stderr)

    result = {
        "metadata": {
            "fetched_at": now.isoformat(),
            "lookback_days": lookback_days,
            "cutoff_date": cutoff_date,
            "repositories": repos,
        },
        "members": member_results,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
