#!/usr/bin/env python3
"""Create a GitLab MR for a Conforma exception/waiver policy.

Uses glab CLI to create the MR in the policy/exception repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create GitLab MR for Conforma exception policy"
    )
    parser.add_argument(
        "--handover",
        required=True,
        help="Path to handover JSON with investigation.violation_analyze",
    )
    parser.add_argument(
        "--output", help="Path to write updated handover (default: stdout)"
    )
    return parser.parse_args()


def validate_prerequisites(handover: dict) -> str | None:
    """Return an error message if prerequisites are not met, else None."""
    investigation = handover.get("investigation", {})
    va = investigation.get("violation_analyze", {})
    if va.get("status") != "completed":
        return (
            "investigation.violation_analyze must be completed "
            "before creating an exception"
        )
    return None


def main() -> int:
    args = parse_args()

    with open(args.handover, encoding="utf-8") as f:
        handover = json.load(f)

    error = validate_prerequisites(handover)
    investigation = handover.setdefault("investigation", {})

    if error:
        investigation["exception_create"] = {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "mr_url": None,
            "exception_policy": None,
            "justification": None,
            "error": error,
        }
    else:
        # TODO: implement glab MR creation
        investigation["exception_create"] = {
            "status": "pending",
            "completed_at": None,
            "mr_url": None,
            "exception_policy": None,
            "justification": None,
            "error": "Not yet implemented",
        }

    output = json.dumps(handover, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
