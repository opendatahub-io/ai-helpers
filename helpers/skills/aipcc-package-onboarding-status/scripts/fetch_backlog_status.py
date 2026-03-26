#!/usr/bin/env python3
"""
Fetch AIPCC package onboarding backlog status with anomaly detection.

Queries all open package onboarding Epics, fetches their child Stories,
and detects workflow anomalies that require human intervention.

Uses acli (Atlassian CLI) for JIRA access. Requires acli to be installed
and authenticated (run 'acli jira auth' first).

Usage:
  fetch_backlog_status.py [--days N] [--jql JQL]

Examples:
  fetch_backlog_status.py
  fetch_backlog_status.py --days 14
  fetch_backlog_status.py --jql 'project = aipcc and ...'
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

JIRA_URL = "https://redhat.atlassian.net"

DEFAULT_JQL = (
    "project = aipcc and labels = package and issuetype = Epic"
    " and status != Closed order by key desc"
)

# Story type detection patterns
STORY_PATTERNS = {
    "builder": re.compile(r"onboard .+ into the aipcc builder", re.IGNORECASE),
    "pipeline": re.compile(r"add .+ into the rhai pipeline onboarding", re.IGNORECASE),
    "qe_testing": re.compile(r"qe testing for package", re.IGNORECASE),
    "probe_test": re.compile(r"probe test", re.IGNORECASE),
}

LIFECYCLE_LABELS = {
    "automation_onboarded": "package-automation-onboarded",
    "build_failed": "package-build-failed",
    "in_test_repo": "package-in-test-repo",
    "in_production_repo": "package-in-production-repo",
    "autoqa_passed": "package-autoqa-passed",
    "autoqa_failed": "package-autoqa-failed",
    "license_incompatible": "package-license-incompatible",
    "builder_onboarded": "package-builder-onboarded",
    "pipeline_onboarded": "package-pipeline-onboarded",
    "probe_tests_created": "package-probe-tests-created",
}


def run_acli(*args: str) -> str:
    """Run an acli command and return stdout."""
    cmd = ["acli", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"acli failed: {result.stderr.strip()}")
    return result.stdout


def acli_search(jql: str, fields: str) -> list[dict]:
    """Search JIRA issues using acli and return parsed JSON."""
    output = run_acli(
        "jira",
        "workitem",
        "search",
        "--jql",
        jql,
        "--json",
        "--paginate",
        "--fields",
        fields,
    )
    if not output.strip():
        return []
    return json.loads(output)


def acli_view(key: str, fields: str) -> dict:
    """View a single JIRA issue using acli and return parsed JSON."""
    output = run_acli(
        "jira",
        "workitem",
        "view",
        key,
        "--json",
        "--fields",
        fields,
    )
    return json.loads(output)


def parse_jira_datetime(dt_str: str) -> datetime | None:
    """Parse a Jira datetime string into a timezone-aware datetime.

    Returns None for empty or unparseable strings instead of a
    sentinel value, so callers can distinguish missing data from
    actual timestamps.
    """
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


def classify_story(summary: str) -> str:
    """Classify a child story by its summary into a known type."""
    for story_type, pattern in STORY_PATTERNS.items():
        if pattern.search(summary):
            return story_type
    return "other"


def extract_package_name(summary: str) -> str:
    """Extract the package name from an epic summary."""
    match = re.match(
        r"^(.+?)\s+package\s+update\s+request",
        summary,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return summary


def days_since(dt_str: str, now: datetime) -> int | None:
    """Calculate days since a datetime string.

    Returns None if the timestamp is missing or unparseable.
    """
    dt = parse_jira_datetime(dt_str)
    if dt is None:
        return None
    return (now - dt).days


def extract_field(issue: dict, field: str, default=""):
    """Safely extract a field from a JIRA issue dict."""
    fields = issue.get("fields", {})
    return fields.get(field, default)


def extract_status(issue: dict) -> str:
    """Extract status name from issue."""
    status = extract_field(issue, "status", {})
    if isinstance(status, dict):
        return status.get("name", "")
    return str(status)


def extract_assignee(issue: dict) -> str:
    """Extract assignee display name from issue."""
    assignee = extract_field(issue, "assignee")
    if isinstance(assignee, dict) and assignee:
        return assignee.get("displayName", "Unassigned")
    return "Unassigned"


def extract_labels(issue: dict) -> list[str]:
    """Extract labels from issue."""
    labels = extract_field(issue, "labels", [])
    return list(labels) if labels else []


def extract_links(issue: dict) -> tuple[list[dict], list[dict]]:
    """Extract blocking relationships from issue links."""
    blocks = []
    blocked_by = []
    links = extract_field(issue, "issuelinks", [])
    for link in links:
        link_type = link.get("type", {})
        if link_type.get("name") != "Blocks":
            continue
        if "outwardIssue" in link:
            out = link["outwardIssue"]
            blocks.append(
                {
                    "key": out["key"],
                    "summary": out["fields"]["summary"],
                    "status": out["fields"]["status"]["name"],
                }
            )
        if "inwardIssue" in link:
            inw = link["inwardIssue"]
            blocked_by.append(
                {
                    "key": inw["key"],
                    "summary": inw["fields"]["summary"],
                    "status": inw["fields"]["status"]["name"],
                }
            )
    return blocks, blocked_by


def fetch_epic_details(key: str) -> dict:
    """Fetch updated/created timestamps for an epic via acli view."""
    try:
        data = acli_view(key, "updated,created")
        return {
            "key": key,
            "updated": extract_field(data, "updated", ""),
            "created": extract_field(data, "created", ""),
        }
    except Exception as e:
        print(
            f"  Warning: could not fetch details for {key}: {e}",
            file=sys.stderr,
        )
        return {
            "key": key,
            "updated": "",
            "created": "",
            "fetch_error": str(e),
        }


def fetch_child_details(key: str) -> dict:
    """Fetch issuelinks and updated for a child story via acli view."""
    try:
        data = acli_view(key, "issuelinks,updated")
        blocks, blocked_by = extract_links(data)
        return {
            "key": key,
            "updated": extract_field(data, "updated", ""),
            "blocks": blocks,
            "blocked_by": blocked_by,
        }
    except Exception as e:
        print(
            f"  Warning: could not fetch links for {key}: {e}",
            file=sys.stderr,
        )
        return {
            "key": key,
            "updated": "",
            "blocks": [],
            "blocked_by": [],
            "fetch_error": str(e),
        }


def fetch_child_stories(epic_key: str) -> list[dict]:
    """Fetch all child stories for an epic using acli search + view."""
    children = []
    seen = set()

    for field in ['"Epic Link"', '"Parent Link"']:
        jql = f"{field} = {epic_key}"
        try:
            results = acli_search(jql, "key,summary,status,labels,assignee")
        except RuntimeError:
            continue

        for issue in results:
            key = issue["key"]
            if key in seen:
                continue
            seen.add(key)

            summary = extract_field(issue, "summary", "")
            children.append(
                {
                    "key": key,
                    "summary": summary,
                    "type": "Story",
                    "story_type": classify_story(summary),
                    "status": extract_status(issue),
                    "assignee": extract_assignee(issue),
                    "labels": extract_labels(issue),
                    "updated": "",
                    "blocks": [],
                    "blocked_by": [],
                }
            )

    # Fetch issuelinks and updated for each child in parallel
    if children:
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(fetch_child_details, c["key"]): c for c in children}
            for future in as_completed(futures):
                child = futures[future]
                details = future.result()
                child["updated"] = details["updated"]
                child["blocks"] = details["blocks"]
                child["blocked_by"] = details["blocked_by"]
                if "fetch_error" in details:
                    child["fetch_error"] = details["fetch_error"]

    return children


def detect_anomalies(
    epic: dict,
    children: list[dict],
    now: datetime,
    stale_days: int,
) -> list[dict]:
    """Detect workflow anomalies for an epic and its children."""
    anomalies = []
    labels = set(epic["labels"])
    status = epic["status"]

    by_type = defaultdict(list)
    for child in children:
        by_type[child["story_type"]].append(child)

    all_children_closed = all(c["status"] == "Closed" for c in children) if children else False
    open_children = [c for c in children if c["status"] != "Closed"]
    closed_children = [c for c in children if c["status"] == "Closed"]

    has = {k: (v in labels) for k, v in LIFECYCLE_LABELS.items()}

    # 1. Epic has package-in-production-repo but not Closed
    if has["in_production_repo"] and status != "Closed" and status != "Review":
        anomalies.append(
            {
                "severity": "high",
                "type": "lifecycle_stuck",
                "message": (
                    f"Epic is '{status}' but has "
                    "'package-in-production-repo' label. "
                    "Should be Closed (or at least Review). "
                    "The lifecycle job may have failed."
                ),
            }
        )

    # 2. All stories closed + autoqa passed + in test repo, not Review
    #    Per lifecycle docs, Review transition requires: status=In Progress,
    #    package-automation-onboarded, package-in-test-repo, package-autoqa-passed,
    #    and ALL child stories Closed.
    if (
        children
        and all_children_closed
        and has["autoqa_passed"]
        and has["in_test_repo"]
        and has["automation_onboarded"]
        and status == "In Progress"
    ):
        anomalies.append(
            {
                "severity": "high",
                "type": "review_not_triggered",
                "message": (
                    f"All {len(children)} child stories are Closed, "
                    "AutoQA passed, package is in test repo, but "
                    f"Epic is still '{status}'. The lifecycle job "
                    "should have moved it to Review."
                ),
            }
        )

    # 3. AutoQA passed but QE Testing story not Closed
    if has["autoqa_passed"]:
        qe_stories = by_type.get("qe_testing", [])
        open_qe = [s for s in qe_stories if s["status"] != "Closed"]
        if open_qe:
            label = "ies are" if len(open_qe) > 1 else "y is"
            anomalies.append(
                {
                    "severity": "medium",
                    "type": "qe_story_inconsistency",
                    "message": (
                        "Epic has 'package-autoqa-passed' but QE "
                        f"Testing stor{label} still "
                        f"'{open_qe[0]['status']}': "
                        + ", ".join(f"{s['key']} ({s['status']})" for s in open_qe)
                    ),
                }
            )

    # 4. AutoQA persistently failing
    if has["autoqa_failed"] and not has["autoqa_passed"]:
        anomalies.append(
            {
                "severity": "medium",
                "type": "autoqa_persistently_failing",
                "message": (
                    "Epic has 'package-autoqa-failed' without "
                    "'package-autoqa-passed'. AutoQA tests are "
                    "persistently failing and may need human "
                    "investigation."
                ),
            }
        )

    # 5. Build failed but no builder story created
    if has["build_failed"] and not by_type.get("builder") and has["automation_onboarded"]:
        anomalies.append(
            {
                "severity": "low",
                "type": "missing_builder_story",
                "message": (
                    "Epic has 'package-build-failed' but no Builder "
                    "onboarding story was created. The "
                    "failure-analysis pipeline may not have "
                    "completed, or the package may be on the "
                    "success path with a transient build failure."
                ),
            }
        )

    # 6. License incompatible
    if has["license_incompatible"]:
        anomalies.append(
            {
                "severity": "high",
                "type": "license_blocked",
                "message": (
                    "Package has incompatible license. Requires "
                    "human decision on whether to proceed with "
                    "license exception or reject."
                ),
            }
        )

    # 7. Stuck in Refinement
    if status == "Refinement":
        epic_age = days_since(epic["updated"], now)
        if epic_age is not None and epic_age > stale_days:
            anomalies.append(
                {
                    "severity": "medium",
                    "type": "stuck_in_refinement",
                    "message": (
                        "Epic has been in Refinement with no update "
                        f"for {epic_age} days. The automation may "
                        "not have picked it up."
                    ),
                }
            )

    # 8. Not started
    if status in ("To Do", "New"):
        anomalies.append(
            {
                "severity": "low",
                "type": "not_started",
                "message": (f"Epic is in '{status}' and has not been picked up by automation yet."),
            }
        )

    # 9. Closed story blocks an open story
    for child in children:
        if child["status"] == "Closed":
            for blocked in child.get("blocks", []):
                if blocked["status"] != "Closed":
                    anomalies.append(
                        {
                            "severity": "info",
                            "type": "blocker_resolved",
                            "message": (
                                f"{child['key']} (Closed) blocks "
                                f"{blocked['key']} "
                                f"({blocked['status']}). Blocker is "
                                "resolved -- downstream story "
                                "should proceed."
                            ),
                        }
                    )

    # 10. Open story blocked by another open story
    for child in children:
        if child["status"] != "Closed":
            for blocker in child.get("blocked_by", []):
                if blocker["status"] != "Closed":
                    anomalies.append(
                        {
                            "severity": "medium",
                            "type": "blocked_story",
                            "message": (
                                f"{child['key']} ({child['status']})"
                                f" is blocked by {blocker['key']} "
                                f"({blocker['status']}). Both are "
                                "open -- upstream work must "
                                "complete first."
                            ),
                        }
                    )

    # 11. Partial completion blocking closure
    if closed_children and open_children and has["autoqa_passed"] and has["in_test_repo"]:
        open_list = ", ".join(f"{c['key']} ({c['status']})" for c in open_children)
        anomalies.append(
            {
                "severity": "high",
                "type": "partial_completion_blocking_closure",
                "message": (
                    f"{len(closed_children)} stories are Closed "
                    f"but {len(open_children)} are still open "
                    f"({open_list}). AutoQA passed and package is "
                    "in test repo, but the lifecycle job cannot "
                    "move Epic to Review until ALL stories are "
                    "Closed."
                ),
            }
        )

    # 12. Duplicate stories of the same type
    for story_type, stories in by_type.items():
        if story_type == "other":
            continue
        if len(stories) > 1:
            story_list = ", ".join(f"{s['key']} ({s['status']})" for s in stories)
            type_name = story_type.replace("_", " ")
            anomalies.append(
                {
                    "severity": "medium",
                    "type": "duplicate_stories",
                    "message": (
                        f"Multiple {type_name} stories found: "
                        f"{story_list}. This may indicate the "
                        "pipeline ran multiple times."
                    ),
                }
            )

    # 13. Staleness
    #     Skip Closed epics. Skip Review epics UNLESS they have
    #     package-in-production-repo (meaning they should have closed
    #     but didn't — production pending closure should still be
    #     flagged stale).
    check_staleness = status != "Closed" and (status != "Review" or has["in_production_repo"])
    if check_staleness:
        epic_stale_days = days_since(epic["updated"], now)
        if epic_stale_days is not None and epic_stale_days > stale_days:
            anomalies.append(
                {
                    "severity": "medium",
                    "type": "stale_epic",
                    "message": (
                        "Epic has had no updates for "
                        f"{epic_stale_days} days "
                        f"(threshold: {stale_days}). May need "
                        "human attention."
                    ),
                }
            )

    return anomalies


def determine_phase(epic: dict, children: list[dict]) -> str:
    """Determine the current phase of the onboarding workflow."""
    labels = set(epic["labels"])
    status = epic["status"]
    has = {k: (v in labels) for k, v in LIFECYCLE_LABELS.items()}

    if status in ("New", "To Do"):
        return "Not Started"
    if status == "Refinement":
        return "Refinement"
    if status == "Review":
        return "Review"
    if status == "Closed":
        return "Closed"

    if has["in_production_repo"]:
        return "Production (pending closure)"
    if has["autoqa_passed"] and has["in_test_repo"]:
        all_closed = all(c["status"] == "Closed" for c in children) if children else False
        if all_closed:
            return "Ready for Review (pending lifecycle)"
        return "QA Passed (stories pending)"
    if has["autoqa_failed"]:
        return "QA Failed"
    if has["in_test_repo"]:
        return "In Test Repo (awaiting QA)"
    if has["build_failed"]:
        by_type = defaultdict(list)
        for c in children:
            by_type[c["story_type"]].append(c)
        if by_type.get("builder"):
            builder_closed = all(s["status"] == "Closed" for s in by_type["builder"])
            if builder_closed:
                return "Builder Done (awaiting pipeline/build)"
            return "Builder Onboarding"
        return "Build Failed (awaiting investigation)"
    if has["license_incompatible"]:
        return "License Blocked"
    if has["automation_onboarded"]:
        return "Automation Running"

    return "In Progress"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help=("Number of days without updates to consider stale (default: 7)"),
    )
    parser.add_argument(
        "--jql",
        type=str,
        default=DEFAULT_JQL,
        help=("JQL query to find epics (default: all open package epics)"),
    )
    args = parser.parse_args()

    if not shutil.which("acli"):
        print(
            "ERROR: acli is not installed or not in PATH. "
            "Install it and run 'acli jira auth' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    now = datetime.now(timezone.utc)

    # Step 1: Search for all matching epics
    print(
        f"Fetching epics with JQL: {args.jql}",
        file=sys.stderr,
    )
    try:
        epic_results = acli_search(args.jql, "key,summary,status,labels,assignee,priority")
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not epic_results:
        print("No epics found.", file=sys.stderr)
        print(
            json.dumps(
                {
                    "results": [],
                    "summary": {
                        "total_epics": 0,
                        "phase_distribution": {},
                        "total_anomalies": 0,
                        "epics_with_anomalies": 0,
                        "anomaly_severity": {},
                    },
                    "metadata": {
                        "fetched_at": now.isoformat(),
                        "stale_threshold_days": args.days,
                        "jql": args.jql,
                        "jira_url": JIRA_URL,
                    },
                },
                indent=2,
            )
        )
        return

    print(
        f"Found {len(epic_results)} epics. Fetching timestamps...",
        file=sys.stderr,
    )

    # Step 2: Fetch updated/created for each epic in parallel
    epic_details = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_epic_details, e["key"]): e["key"] for e in epic_results}
        for future in as_completed(futures):
            details = future.result()
            epic_details[details["key"]] = details

    # Build epic dicts
    all_epics = []
    for issue in epic_results:
        key = issue["key"]
        details = epic_details.get(key, {})
        summary = extract_field(issue, "summary", "")
        epic_dict = {
            "key": key,
            "summary": summary,
            "package_name": extract_package_name(summary),
            "status": extract_status(issue),
            "assignee": extract_assignee(issue),
            "labels": extract_labels(issue),
            "updated": details.get("updated", ""),
            "created": details.get("created", ""),
            "priority": (
                extract_field(issue, "priority", {}).get("name", "Undefined")
                if isinstance(extract_field(issue, "priority"), dict)
                else "Undefined"
            ),
        }
        if "fetch_error" in details:
            epic_dict["fetch_error"] = details["fetch_error"]
        all_epics.append(epic_dict)

    print(
        f"Fetching children for {len(all_epics)} epics...",
        file=sys.stderr,
    )

    # Step 3: For each epic, fetch children and detect anomalies
    results = []
    for i, epic in enumerate(all_epics):
        print(
            f"  [{i + 1}/{len(all_epics)}] {epic['key']} ({epic['package_name']})",
            file=sys.stderr,
        )

        children = fetch_child_stories(epic["key"])
        anomalies = detect_anomalies(epic, children, now, args.days)
        phase = determine_phase(epic, children)

        results.append(
            {
                "epic": epic,
                "children": children,
                "anomalies": anomalies,
                "phase": phase,
                "children_summary": {
                    "total": len(children),
                    "closed": len([c for c in children if c["status"] == "Closed"]),
                    "open": len([c for c in children if c["status"] != "Closed"]),
                    "types": dict(
                        defaultdict(
                            int,
                            {
                                t: len([c for c in children if c["story_type"] == t])
                                for t in set(c["story_type"] for c in children)
                            },
                        )
                    ),
                },
            }
        )

    # Compute summary statistics
    phase_counts = defaultdict(int)
    severity_counts = defaultdict(int)
    total_anomalies = 0
    epics_with_anomalies = 0

    for r in results:
        phase_counts[r["phase"]] += 1
        if r["anomalies"]:
            epics_with_anomalies += 1
            for a in r["anomalies"]:
                severity_counts[a["severity"]] += 1
                total_anomalies += 1

    output = {
        "results": results,
        "summary": {
            "total_epics": len(all_epics),
            "phase_distribution": dict(phase_counts),
            "total_anomalies": total_anomalies,
            "epics_with_anomalies": epics_with_anomalies,
            "anomaly_severity": dict(severity_counts),
        },
        "metadata": {
            "fetched_at": now.isoformat(),
            "stale_threshold_days": args.days,
            "jql": args.jql,
            "jira_url": JIRA_URL,
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
