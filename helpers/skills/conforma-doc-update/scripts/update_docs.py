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
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Document verified solutions into violation YAML files"
    )
    parser.add_argument(
        "--handover",
        required=True,
        help="Path to handover JSON with successful rerun",
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
    rerun = investigation.get("rerun", {})
    if rerun.get("status") != "completed":
        return "investigation.rerun must be completed before updating docs"
    if rerun.get("result") != "pass":
        return 'investigation.rerun.result must be "pass" to document the solution'
    return None


def main() -> int:
    args = parse_args()

    handover = _safe_open_handover(args.handover)

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
        _safe_write_output(args.output, output)
    else:
        print(output)

    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
