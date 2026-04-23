#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///
"""
Analyze a Jira Plan CSV export to measure work distribution against org targets.

Reads a CSV exported from Jira Plans (portfolio view), classifies each work
item into one of three categories (Tech Debt & Quality, New Features, Learning
& Enablement), and produces a JSON report comparing actual distribution against
the organizational target of 40/40/20.

Classification uses a rule-based approach with confidence levels. Items that
cannot be confidently classified are flagged for AI review.

Usage:
  analyze_plan_balance.py <csv-file> [--hierarchy Epic,Feature]
  analyze_plan_balance.py <csv-file> [--team "Frank's Team"]

Examples:
  analyze_plan_balance.py portfolio_overview.csv
  analyze_plan_balance.py portfolio_overview.csv --hierarchy Epic
  analyze_plan_balance.py portfolio_overview.csv --team "Antonio's Team"
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone

TARGETS = {
    "tech_debt": 40,
    "new_features": 40,
    "learning": 20,
}

CATEGORY_LABELS = {
    "tech_debt": "Tech Debt & Quality",
    "new_features": "New Features",
    "learning": "Learning & Enablement",
}

TECH_DEBT_LABEL_PATTERNS = [
    "tech-debt",
    "support",
    "package-build-failed",
    "package-security-blocked",
    "package-autoqa-failed",
]

TECH_DEBT_TITLE_PATTERNS = [
    r"\bbug\b",
    r"\bfix(ed|es|ing)?\s+(bug|issue|error|crash|fail|regression|flaw|leak)",
    r"\bflak[ey]",
    r"\btest\s*(coverage|infra|framework|automation|stability)",
    r"\bstabil",
    r"\bquality\b",
    r"\bdebt\b",
    r"\bsecur",
    r"\bpatch\b",
    r"\bupgrade\b",
    r"\bmigrat",
    r"\brefactor",
    r"\bdeprecat",
    r"\breliab",
    r"\bmaintain",
    r"\bCVE\b",
    r"\bvulnerabil",
    r"\bclean[\s-]?up",
    r"\bcompli[ae]nce",
    r"\btechnical\s+debt",
    r"\bbug\s*bash",
    r"\bregression",
    r"\bbackport",
    r"\bhotfix",
    r"\berrata\b",
    r"\bCPaaS\b",
    r"\bbuild\s*(failure|broken|fix)",
    r"\bCI\s*(fix|failure|broken|stab)",
    r"\bpackage\s+(update|upgrade|rebuild|build)",
]

LEARNING_TITLE_PATTERNS = [
    r"\bspike\b",
    r"\btrain(ing)?\b",
    r"\blearn(ing)?\b",
    r"\bresearch\b",
    r"\benablement\b",
    r"\bexplor[ea]",
    r"\bPOC\b",
    r"\bproof\s+of\s+concept",
    r"\bprototyp",
    r"\binvestigat",
    r"\bstudy\b",
    r"\bexperiment",
    r"\bhackathon",
    r"\bworkshop",
    r"\bonboard",
    r"\beducat",
    r"\bramp\b",
    r"\bAI\s*(research|enablement|adoption)",
    r"\bADLC\b",
]

ACTIVE_STATUSES = {"In Progress", "Review"}


def classify_item(row):
    """Classify a work item into a category with confidence."""
    title = row.get("Title", "").lower()
    labels = row.get("Labels", "").lower()
    hierarchy = row.get("Hierarchy", "")

    label_list = [lbl.strip() for lbl in labels.split(",") if lbl.strip()]

    for pattern in TECH_DEBT_LABEL_PATTERNS:
        if pattern in label_list:
            return "tech_debt", "high", f"label match: {pattern}"

    for pattern in LEARNING_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return "learning", "medium", f"title match: {pattern}"

    for pattern in TECH_DEBT_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return "tech_debt", "medium", f"title match: {pattern}"

    if hierarchy == "Bug":
        return "tech_debt", "high", "issue type: Bug"

    return "new_features", "low", "default classification"


def parse_estimate(value):
    """Parse an estimate value, returning None if empty or invalid."""
    if not value or not value.strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


def compute_distribution(items, use_estimates=False):
    """Compute category distribution from a list of classified items."""
    counts = {"tech_debt": 0, "new_features": 0, "learning": 0}
    weighted = {"tech_debt": 0.0, "new_features": 0.0, "learning": 0.0}

    for item in items:
        cat = item["category"]
        counts[cat] += 1
        if use_estimates and item.get("estimate") is not None:
            weighted[cat] += item["estimate"]

    total_count = sum(counts.values())
    total_weighted = sum(weighted.values())

    result = {}
    for cat in ["tech_debt", "new_features", "learning"]:
        entry = {
            "label": CATEGORY_LABELS[cat],
            "count": counts[cat],
            "count_pct": round(counts[cat] / total_count * 100, 1) if total_count > 0 else 0,
            "target_pct": TARGETS[cat],
        }
        if use_estimates and total_weighted > 0:
            entry["estimate_days"] = round(weighted[cat], 1)
            entry["estimate_pct"] = round(weighted[cat] / total_weighted * 100, 1)
        entry["delta"] = round(entry["count_pct"] - TARGETS[cat], 1)
        result[cat] = entry

    result["_totals"] = {"count": total_count}
    if use_estimates and total_weighted > 0:
        result["_totals"]["estimate_days"] = round(total_weighted, 1)

    return result


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("csv_file", help="Path to Jira Plan CSV export")
    parser.add_argument(
        "--hierarchy",
        help="Comma-separated hierarchy types to include (e.g., Epic,Feature). Default: all.",
    )
    parser.add_argument(
        "--team",
        help="Filter to a specific team.",
    )
    args = parser.parse_args()

    hierarchy_filter = None
    if args.hierarchy:
        hierarchy_filter = {h.strip() for h in args.hierarchy.split(",")}

    try:
        with open(args.csv_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"ERROR: CSV file not found: {args.csv_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}", file=sys.stderr)
        sys.exit(1)

    items = []
    for rank, row in enumerate(rows, start=1):
        hierarchy = row.get("Hierarchy", "")
        if hierarchy_filter and hierarchy not in hierarchy_filter:
            continue

        team = row.get("Team", "") or row.get("Team (roll-up)", "")
        if args.team and args.team.lower() != team.lower():
            continue

        category, confidence, reason = classify_item(row)
        estimate = parse_estimate(row.get("Estimates (d)", ""))
        labels = [lbl.strip() for lbl in row.get("Labels", "").split(",") if lbl.strip()]

        item = {
            "priority_rank": rank,
            "key": row.get("Work item key", ""),
            "hierarchy": hierarchy,
            "title": row.get("Title", ""),
            "team": team,
            "assignee": row.get("Assignee", ""),
            "status": row.get("Work item status", ""),
            "priority": row.get("Priority", ""),
            "labels": labels,
            "estimate": estimate,
            "progress_pct": row.get("Progress (%)", ""),
            "category": category,
            "confidence": confidence,
            "classification_reason": reason,
        }
        items.append(item)

    has_estimates = any(item.get("estimate") is not None for item in items)

    active_items = [i for i in items if i["status"] in ACTIVE_STATUSES]

    teams = sorted({i["team"] for i in items if i["team"]})
    by_team = {}
    for team in teams:
        team_items = [i for i in items if i["team"] == team]
        by_team[team] = compute_distribution(team_items, use_estimates=has_estimates)

    n = len(items)
    quartile_size = n // 4 if n >= 4 else n
    bands = {}
    if n > 0:
        bands["top_quartile"] = compute_distribution(
            items[:quartile_size], use_estimates=has_estimates
        )
        bands["second_quartile"] = compute_distribution(
            items[quartile_size : quartile_size * 2], use_estimates=has_estimates
        )
        bands["third_quartile"] = compute_distribution(
            items[quartile_size * 2 : quartile_size * 3], use_estimates=has_estimates
        )
        bands["bottom_quartile"] = compute_distribution(
            items[quartile_size * 3 :], use_estimates=has_estimates
        )

    low_confidence = [
        {
            "key": i["key"],
            "title": i["title"],
            "category": i["category"],
            "reason": i["classification_reason"],
        }
        for i in items
        if i["confidence"] == "low"
    ]

    result = {
        "items": items,
        "distribution": {
            "all_items": compute_distribution(items, use_estimates=has_estimates),
            "active_items": compute_distribution(active_items, use_estimates=has_estimates),
            "by_priority_band": bands,
            "by_team": by_team,
        },
        "targets": {k: {"pct": v, "label": CATEGORY_LABELS[k]} for k, v in TARGETS.items()},
        "low_confidence_count": len(low_confidence),
        "low_confidence_items": low_confidence,
        "metadata": {
            "csv_file": args.csv_file,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "total_rows_in_csv": len(rows),
            "items_analyzed": len(items),
            "hierarchy_filter": list(hierarchy_filter) if hierarchy_filter else None,
            "team_filter": args.team,
            "has_estimates": has_estimates,
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
