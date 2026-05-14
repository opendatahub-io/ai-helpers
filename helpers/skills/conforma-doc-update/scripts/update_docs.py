#!/usr/bin/env python3
"""Document verified solutions into per-violation YAML files.

Appends resolved_cases to existing files or creates new violation
YAML files for undocumented violations.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Document verified solutions into violation YAML files"
    )
    parser.add_argument(
        "--handover",
        required=True,
        help="Path to handover JSON with successful rerun",
    )
    parser.add_argument(
        "--output", help="Path to write updated handover (default: stdout)"
    )
    return parser.parse_args()


def validate_prerequisites(handover: dict) -> str | None:
    """Return an error message if prerequisites are not met, else None."""
    investigation = handover.get("investigation", {})
    rerun = investigation.get("rerun", {})
    if rerun.get("status") != "completed":
        return "investigation.rerun must be completed before updating docs"
    if rerun.get("result") != "pass":
        return 'investigation.rerun.result must be "pass" to document the solution'
    return None


def main() -> int:
    args = parse_args()

    with open(args.handover, encoding="utf-8") as f:
        handover = json.load(f)

    error = validate_prerequisites(handover)
    investigation = handover.setdefault("investigation", {})

    if error:
        investigation["doc_update"] = {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "violation_file": None,
            "update_type": None,
            "resolved_case_added": None,
            "error": error,
        }
    else:
        # TODO: implement YAML file update/creation logic
        investigation["doc_update"] = {
            "status": "pending",
            "completed_at": None,
            "violation_file": None,
            "update_type": None,
            "resolved_case_added": None,
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
