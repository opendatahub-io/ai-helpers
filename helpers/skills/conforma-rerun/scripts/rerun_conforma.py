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
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trigger rebuild and verify Conforma result")
    parser.add_argument(
        "--handover",
        required=True,
        help="Path to handover JSON with completed fix or exception",
    )
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

    handover = _safe_open_handover(args.handover)

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
        _safe_write_output(args.output, output)
    else:
        print(output)

    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
