#!/usr/bin/env python3
"""Fetch a Conforma report from the Tekton Results API.

Wraps existing rhoai-monitoring fetch script with structured JSON output.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Conforma report from Tekton Results API")
    parser.add_argument("--namespace", required=True, help="Kubernetes namespace")
    parser.add_argument("--pipeline-run", help="Specific PipelineRun name")
    parser.add_argument("--component", help="Filter to a specific component")
    parser.add_argument("--handover", help="Path to existing handover JSON to update")
    parser.add_argument("--output", help="Path to write updated handover (default: stdout)")
    return parser.parse_args()


def _validate_path(path_str: str) -> Path:
    """Validate a file path against traversal attacks."""
    raw = Path(path_str)
    if ".." in raw.parts:
        print(f"Error: path traversal detected: {path_str}", file=sys.stderr)
        sys.exit(1)
    return raw.resolve()


def main() -> int:
    args = parse_args()

    handover: dict = {}
    if args.handover:
        resolved = _validate_path(args.handover)
        try:
            with open(resolved, encoding="utf-8") as f:
                handover = json.load(f)
        except FileNotFoundError:
            print(f"Error: handover file not found: {args.handover}", file=sys.stderr)
            return 1
        except PermissionError:
            print(f"Error: permission denied: {args.handover}", file=sys.stderr)
            return 1
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in {args.handover}: {exc}", file=sys.stderr)
            return 1

    handover.setdefault("metadata", {})
    handover["metadata"]["namespace"] = args.namespace
    if args.pipeline_run:
        handover["metadata"]["pipeline_run"] = args.pipeline_run
    handover["metadata"]["created_at"] = datetime.now(timezone.utc).isoformat()

    # TODO: integrate existing Tekton Results API fetch script
    handover["report_fetch"] = {
        "status": "pending",
        "completed_at": None,
        "raw_report_path": None,
        "error": "Not yet implemented -- wire existing rhoai-monitoring script here",
    }

    output = json.dumps(handover, indent=2)
    if args.output:
        resolved_out = _validate_path(args.output)
        try:
            resolved_out.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved_out, "w", encoding="utf-8") as f:
                f.write(output)
        except PermissionError:
            print(f"Error: permission denied writing: {args.output}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"Error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 1
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
