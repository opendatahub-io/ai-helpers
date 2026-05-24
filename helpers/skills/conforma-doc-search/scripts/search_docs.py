#!/usr/bin/env python3
"""Look up troubleshooting documentation for a Conforma violation.

Performs deterministic YAML file lookup by violation code with
pattern-based fallback search.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"
VIOLATIONS_DIR = REFERENCES_DIR / "violations"

_SAFE_CODE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Look up violation documentation by code")
    parser.add_argument(
        "--handover",
        required=True,
        help="Path to handover JSON with investigation.violation",
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
    if not investigation.get("violation"):
        return "investigation.violation must be selected before searching docs"
    return None


def lookup_exact(violation_code: str) -> Path | None:
    """Try direct filename lookup."""
    if not violation_code or not _SAFE_CODE_RE.match(violation_code):
        return None
    candidate = VIOLATIONS_DIR / f"{violation_code}.yaml"
    if candidate.is_file():
        return candidate
    return None


def lookup_pattern(msg: str) -> list[Path]:
    """Fallback: search patterns fields across all YAML files."""
    # TODO: implement pattern matching across violation YAML files
    _ = msg
    return []


def main() -> int:
    args = parse_args()

    handover = _safe_open_handover(args.handover)

    error = validate_prerequisites(handover)
    investigation = handover.setdefault("investigation", {})

    if error:
        investigation["doc_search"] = {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "violation_file": None,
            "violation_data": None,
            "related_files": [],
            "match_type": "none",
            "error": error,
        }
    else:
        violation = investigation["violation"]
        violation_code = violation.get("violation_code", "")
        msg = violation.get("msg", "")

        exact_path = lookup_exact(violation_code)
        if exact_path:
            # TODO: parse the YAML file and populate violation_data
            investigation["doc_search"] = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "violation_file": str(exact_path),
                "violation_data": None,
                "related_files": [],
                "match_type": "exact",
                "error": None,
            }
        else:
            pattern_matches = lookup_pattern(msg)
            investigation["doc_search"] = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "violation_file": str(pattern_matches[0]) if pattern_matches else None,
                "violation_data": None,
                "related_files": [str(p) for p in pattern_matches[1:]],
                "match_type": "pattern" if pattern_matches else "none",
                "error": None,
            }

    output = json.dumps(handover, indent=2)
    if args.output:
        _safe_write_output(args.output, output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
