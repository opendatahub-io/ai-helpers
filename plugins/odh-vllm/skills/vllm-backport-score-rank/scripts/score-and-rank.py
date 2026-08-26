#!/usr/bin/env python3
"""
Score and rank backport candidates using a composite formula.

Reads analyzed.json (candidates with agent-added semantic fields) and outputs
ranked.json sorted by score descending.

Usage:
  python3 scripts/score-and-rank.py \
    --input artifacts/backport-triage/analyzed.json \
    --output artifacts/backport-triage/ranked.json
"""

import argparse
import json
import sys

VERDICT_SCORE = {
    "must_backport": 30,
    "likely_relevant": 20,
    "needs_review": 10,
    "likely_skip": 0,
    "skip": 0,
}

SEVERITY_SCORE = {
    "critical": 25,
    "moderate": 15,
    "low": 5,
}

SCOPE_SCORE = {
    "all_users": 20,
    "specific_models": 12,
    "specific_feature": 8,
    "edge_case": 3,
}

RISK_SCORE = {
    "safe": 15,
    "moderate": 8,
    "risky": 0,
}


def compute_score(pr):
    v = VERDICT_SCORE.get(pr.get("verdict", ""), 0)
    s = SEVERITY_SCORE.get(pr.get("severity", ""), 0)
    sc = SCOPE_SCORE.get(pr.get("affected_scope", ""), 0)
    r = RISK_SCORE.get(pr.get("backport_risk", ""), 0)
    self_contained = 10 if pr.get("self_contained") else 0
    return v + s + sc + r + self_contained


def main():
    parser = argparse.ArgumentParser(description="Score and rank backport candidates")
    parser.add_argument("--input", required=True, help="Path to analyzed.json")
    parser.add_argument("--output", required=True, help="Output path for ranked.json")
    args = parser.parse_args()

    with open(args.input) as f:
        prs = json.load(f)

    candidates = [
        pr
        for pr in prs
        if not pr.get("already_backported")
        and pr.get("verdict") not in ("SKIP", "skip", "likely_skip")
    ]

    for pr in candidates:
        pr["score"] = compute_score(pr)
        size = pr.get("additions", 0) + pr.get("deletions", 0)
        pr["change_size"] = size
        pr["backport_ease"] = (
            "ai-fixable"
            if pr.get("self_contained") and pr.get("backport_risk") in ("safe", "moderate")
            else "ai-nonfixable"
        )

    ranked = sorted(
        candidates,
        key=lambda r: (
            -r["score"],
            -r.get("files_in_release_count", 0),
            r["change_size"],
        ),
    )

    for i, pr in enumerate(ranked):
        pr["rank"] = i + 1

    with open(args.output, "w") as f:
        json.dump(ranked, f, indent=2)

    bins = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for pr in ranked:
        s = pr["score"]
        if s >= 90:
            bins["critical"] += 1
        elif s >= 70:
            bins["high"] += 1
        elif s >= 50:
            bins["medium"] += 1
        else:
            bins["low"] += 1

    print(f"Ranked {len(ranked)} candidates (from {len(prs)} total)", file=sys.stderr)
    print(f"  Critical (>=90): {bins['critical']}", file=sys.stderr)
    print(f"  High (70-89):    {bins['high']}", file=sys.stderr)
    print(f"  Medium (50-69):  {bins['medium']}", file=sys.stderr)
    print(f"  Low (<50):       {bins['low']}", file=sys.stderr)
    print(f"Output: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
