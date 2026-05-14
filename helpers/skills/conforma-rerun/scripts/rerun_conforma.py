#!/usr/bin/env python3
"""Trigger a pipeline rebuild and verify the Conforma result.

Triggers the build, polls for completion, fetches the new Conforma
verification result, and compares pass/fail.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trigger rebuild and verify Conforma result"
    )
    parser.add_argument(
        "--handover",
        required=True,
        help="Path to handover JSON with completed fix or exception",
    )
    parser.add_argument(
        "--output", help="Path to write updated handover (default: stdout)"
    )
    return parser.parse_args()


def validate_prerequisites(handover: dict) -> str | None:
    """Return an error message if prerequisites are not met, else None."""
    investigation = handover.get("investigation", {})
    fix = investigation.get("fix_apply", {})
    exc = investigation.get("exception_create", {})
    if fix.get("status") != "completed" and exc.get("status") != "completed":
        return (
            "Either investigation.fix_apply or investigation.exception_create "
            "must be completed before rerunning"
        )
    return None


def main() -> int:
    args = parse_args()

    with open(args.handover, encoding="utf-8") as f:
        handover = json.load(f)

    error = validate_prerequisites(handover)
    investigation = handover.setdefault("investigation", {})

    if error:
        investigation["rerun"] = {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "new_pipeline_run": None,
            "result": None,
            "new_violations": [],
            "error": error,
        }
    else:
        # TODO: implement pipeline trigger + poll + result fetch
        investigation["rerun"] = {
            "status": "pending",
            "completed_at": None,
            "new_pipeline_run": None,
            "result": "pending",
            "new_violations": [],
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
