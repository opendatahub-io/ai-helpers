#!/usr/bin/env python3
"""Parse a Conforma report YAML into structured violation JSON.

This is the critical handoff point -- all downstream skills depend on
this parser's structured output.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Conforma report into structured violations JSON"
    )
    parser.add_argument("--handover", required=True, help="Path to handover JSON with report_fetch")
    parser.add_argument("--output", help="Path to write updated handover (default: stdout)")
    return parser.parse_args()


def _safe_open_handover(path_str: str) -> dict:
    """Open and parse handover JSON with path validation."""
    raw = Path(path_str)
    if ".." in raw.parts:
        print(f"Error: path traversal detected: {path_str}", file=sys.stderr)
        sys.exit(1)
    resolved = raw.resolve()
    try:
        with open(resolved, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: handover file not found: {path_str}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: permission denied: {path_str}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {path_str}: {exc}", file=sys.stderr)
        sys.exit(1)


def _safe_write_output(path_str: str, data: str) -> None:
    """Write output with path validation."""
    raw = Path(path_str)
    if ".." in raw.parts:
        print(f"Error: path traversal detected: {path_str}", file=sys.stderr)
        sys.exit(1)
    resolved = raw.resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved, "w", encoding="utf-8") as f:
        f.write(data)


def validate_prerequisites(handover: dict) -> str | None:
    """Return an error message if prerequisites are not met, else None."""
    report_fetch = handover.get("report_fetch", {})
    if report_fetch.get("status") != "completed":
        return "report_fetch must be completed before parsing violations"
    if not report_fetch.get("raw_report_path"):
        return "report_fetch.raw_report_path is missing"
    return None


def main() -> int:
    args = parse_args()

    handover = _safe_open_handover(args.handover)

    error = validate_prerequisites(handover)
    if error:
        handover["violation_parse"] = {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "violations": [],
            "violation_count": 0,
            "error": error,
        }
    else:
        # TODO: implement YAML parsing of the Conforma report
        # Read handover["report_fetch"]["raw_report_path"]
        # Extract violations into the structured format
        handover["violation_parse"] = {
            "status": "pending",
            "completed_at": None,
            "violations": [],
            "violation_count": 0,
            "error": "Not yet implemented -- build the YAML parser here",
        }

    output = json.dumps(handover, indent=2)
    if args.output:
        _safe_write_output(args.output, output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
