#!/usr/bin/env python3
"""Create a GitLab MR for a Conforma exception/waiver policy.

Supports two modes:
  - Pipeline mode: reads all context from a handover JSON document
  - Standalone mode: accepts individual CLI arguments provided by the user

Uses glab CLI to create the MR in the policy/exception repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create GitLab MR for Conforma exception policy")

    parser.add_argument(
        "--handover",
        help="Path to handover JSON (pipeline mode). "
        "If omitted, standalone arguments are required.",
    )
    parser.add_argument("--output", help="Path to write updated handover (default: stdout)")

    standalone = parser.add_argument_group(
        "standalone arguments",
        "Required when --handover is not provided.",
    )
    standalone.add_argument(
        "--container-image",
        help="Full container image reference being exempted (e.g. quay.io/org/image@sha256:abc...)",
    )
    standalone.add_argument(
        "--component",
        help="Component name (e.g. my-component)",
    )
    standalone.add_argument(
        "--rule",
        help="Policy rule to create an exception for (e.g. attestation_task.sbom_task_present)",
    )
    standalone.add_argument(
        "--effective-until",
        help="Expiry date for the exception in YYYY-MM-DD format",
    )
    standalone.add_argument(
        "--jira-url",
        help="URL of the JIRA ticket justifying this exception",
    )
    standalone.add_argument(
        "--justification",
        help="Reason why the exception is needed",
    )
    standalone.add_argument(
        "--policy-repo",
        help="GitLab project path for the exception policy repo (e.g. org/conforma-exceptions)",
    )

    return parser.parse_args()


def _validate_path(path_str: str) -> Path:
    """Validate a file path against traversal attacks."""
    raw = Path(path_str)
    if ".." in raw.parts:
        print(f"Error: path traversal detected: {path_str}", file=sys.stderr)
        sys.exit(1)
    return raw.resolve()


def validate_handover_mode(handover: dict) -> list[str]:
    """Validate prerequisites when running in pipeline/handover mode."""
    errors: list[str] = []
    investigation = handover.get("investigation", {})
    va = investigation.get("violation_analyze", {})
    if va.get("status") != "completed":
        errors.append(
            "investigation.violation_analyze must have status 'completed' "
            "before creating an exception"
        )

    violation = investigation.get("violation", {})
    if not violation.get("rule"):
        errors.append(
            "investigation.violation.rule is missing — cannot determine which policy rule to exempt"
        )

    return errors


STANDALONE_REQUIRED = {
    "--container-image": "container_image",
    "--rule": "rule",
    "--effective-until": "effective_until",
    "--jira-url": "jira_url",
    "--justification": "justification",
}


def validate_standalone_mode(args: argparse.Namespace) -> list[str]:
    """Validate that all required standalone arguments are present and valid."""
    errors: list[str] = []

    for flag, attr in STANDALONE_REQUIRED.items():
        if not getattr(args, attr, None):
            errors.append(f"{flag} is required in standalone mode")

    if errors:
        return errors

    effective_until = getattr(args, "effective_until", None)
    if effective_until:
        try:
            expiry = datetime.strptime(effective_until, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            errors.append(f"--effective-until must be YYYY-MM-DD format, got: {effective_until}")
            return errors

        if expiry.date() <= datetime.now(timezone.utc).date():
            errors.append(f"--effective-until must be a future date, got: {effective_until}")

    return errors


def build_handover_from_args(args: argparse.Namespace) -> dict:
    """Build a minimal handover-compatible structure from standalone args."""
    return {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": "standalone",
        },
        "investigation": {
            "violation": {
                "component": args.component or "unknown",
                "container_image": args.container_image,
                "rule": args.rule,
            },
            "violation_analyze": {
                "status": "completed",
            },
            "standalone_inputs": {
                "effective_until": args.effective_until,
                "jira_url": args.jira_url,
                "justification": args.justification,
                "policy_repo": args.policy_repo,
            },
        },
    }


def write_result(handover: dict, output_path: str | None) -> None:
    result = json.dumps(handover, indent=2)
    if output_path:
        resolved = _validate_path(output_path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)


def main() -> int:
    args = parse_args()

    is_pipeline_mode = args.handover is not None

    if is_pipeline_mode:
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
        errors = validate_handover_mode(handover)
    else:
        errors = validate_standalone_mode(args)
        if not errors:
            handover = build_handover_from_args(args)

    if errors:
        error_msg = "; ".join(errors)
        if is_pipeline_mode:
            investigation = handover.setdefault("investigation", {})
            investigation["exception_create"] = {
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "mr_url": None,
                "exception_policy": None,
                "justification": None,
                "error": error_msg,
            }
            write_result(handover, args.output)
        else:
            print(f"Error: {error_msg}", file=sys.stderr)
        return 1

    investigation = handover.setdefault("investigation", {})

    # TODO: implement glab MR creation
    # - generate exception policy YAML
    # - create branch, commit, push
    # - glab mr create
    investigation["exception_create"] = {
        "status": "pending",
        "completed_at": None,
        "mr_url": None,
        "exception_policy": investigation.get("violation", {}).get("rule"),
        "justification": (
            investigation.get("standalone_inputs", {}).get("justification")
            if not is_pipeline_mode
            else None
        ),
        "error": "Not yet implemented",
    }

    write_result(handover, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
