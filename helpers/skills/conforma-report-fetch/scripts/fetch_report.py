#!/usr/bin/env python3
"""Fetch a Conforma report from the Tekton Results API.

Wraps existing rhoai-monitoring fetch script with structured JSON output.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Conforma report from Tekton Results API"
    )
    parser.add_argument("--namespace", required=True, help="Kubernetes namespace")
    parser.add_argument("--pipeline-run", help="Specific PipelineRun name")
    parser.add_argument("--component", help="Filter to a specific component")
    parser.add_argument("--handover", help="Path to existing handover JSON to update")
    parser.add_argument(
        "--output", help="Path to write updated handover (default: stdout)"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    handover: dict = {}
    if args.handover:
        with open(args.handover, encoding="utf-8") as f:
            handover = json.load(f)

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
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
