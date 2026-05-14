#!/usr/bin/env python3
"""Fetch component build logs from the Tekton Results API.

Wraps existing rhoai-monitoring log fetch script with structured JSON output.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch component build logs from Tekton Results API"
    )
    parser.add_argument(
        "--handover",
        required=True,
        help="Path to handover JSON with investigation.violation",
    )
    parser.add_argument(
        "--output", help="Path to write updated handover (default: stdout)"
    )
    return parser.parse_args()


def validate_prerequisites(handover: dict) -> str | None:
    """Return an error message if prerequisites are not met, else None."""
    vp = handover.get("violation_parse", {})
    if vp.get("status") != "completed":
        return "violation_parse must be completed before fetching logs"
    investigation = handover.get("investigation", {})
    if not investigation.get("violation"):
        return "investigation.violation must be selected before fetching logs"
    return None


def main() -> int:
    args = parse_args()

    with open(args.handover, encoding="utf-8") as f:
        handover = json.load(f)

    error = validate_prerequisites(handover)
    investigation = handover.setdefault("investigation", {})

    if error:
        investigation["logs_fetch"] = {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "logs": "",
            "log_lines": 0,
            "error": error,
        }
    else:
        # TODO: integrate existing Tekton Results API log fetch script
        investigation["logs_fetch"] = {
            "status": "pending",
            "completed_at": None,
            "logs": "",
            "log_lines": 0,
            "error": "Not yet implemented -- wire existing rhoai-monitoring script here",
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
