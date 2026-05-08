#!/usr/bin/env python3
"""Generate EPIC artifact files and/or Jira JSON for accelerator variant releases.

Reads template definitions from epic-templates.yaml, resolves placeholders,
and writes output files in one of two formats:

- artifact: per-EPIC markdown files with YAML frontmatter (epic-creator compatible)
- jira: JSON files for ``acli jira workitem create --from-json``

Usage:
    python3 generate_epics.py \\
        --templates references/epic-templates.yaml \\
        --accelerator cuda --accel-version "CUDA 12.9" \\
        --variant cuda12.9-ubi9 --release "3.5 EA1" \\
        --torch-version 2.10 --vllm-version 0.19.1 \\
        --parent-feature AIPCC-XXXX --hardware-type "NVIDIA GPU" \\
        --mode both --output-dir artifacts/epic-tasks
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import textwrap
from pathlib import Path

import yaml


def load_templates(path: Path) -> dict:
    """Load and validate the epic-templates.yaml file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for key in ("accelerators", "templates", "jira"):
        if key not in data:
            print(f"Error: missing required key '{key}' in {path}", file=sys.stderr)
            sys.exit(1)
    return data


def select_template(
    config: dict, accelerator: str, accel_version: str
) -> tuple[str, list[dict], list[dict]]:
    """Return (template_name, epics, optional_epics) for the accelerator."""
    accel_def = config["accelerators"].get(accelerator)
    if not accel_def:
        valid = ", ".join(sorted(config["accelerators"]))
        print(
            f"Error: unknown accelerator '{accelerator}'. Valid: {valid}",
            file=sys.stderr,
        )
        sys.exit(1)

    template_name = accel_def["default_template"]

    for rule in accel_def.get("template_rules", []):
        if "match_version_ge" in rule:
            version_num = extract_version_number(accel_version)
            if version_num is not None and version_num >= rule["match_version_ge"]:
                template_name = rule["template"]
                break

    template = config["templates"].get(template_name)
    if not template:
        print(
            f"Error: template '{template_name}' not found in templates",
            file=sys.stderr,
        )
        sys.exit(1)

    return template_name, template["epics"], template.get("optional_epics", [])


def extract_version_number(accel_version: str) -> float | None:
    """Extract the leading numeric version from a string like 'CUDA 12.9'."""
    match = re.search(r"(\d+(?:\.\d+)?)", accel_version)
    if match:
        return float(match.group(1))
    return None


def resolve_placeholders(text: str, params: dict[str, str]) -> str:
    """Replace {placeholder} tokens with parameter values."""
    result = text
    for key, value in params.items():
        result = result.replace(f"{{{key}}}", value)
    remaining = re.findall(r"\{(\w+)\}", result)
    if remaining:
        print(f"Warning: unresolved placeholders: {remaining}", file=sys.stderr)
    return result


def build_params(args: argparse.Namespace) -> dict[str, str]:
    """Build the placeholder parameters dict from CLI arguments."""
    params: dict[str, str] = {
        "accelerator": args.accelerator,
        "accel_version": args.accel_version,
        "variant": args.variant,
        "release": args.release,
        "hardware_type": args.hardware_type,
        "parent_feature": args.parent_feature,
    }
    if args.torch_version:
        params["torch_version"] = args.torch_version
    if args.vllm_version:
        params["vllm_version"] = args.vllm_version
    if args.sendnn_constraints:
        params["sendnn_constraints"] = args.sendnn_constraints
    return params


def build_epic_list(
    epics: list[dict],
    optional_epics: list[dict],
    params: dict[str, str],
) -> list[dict[str, str]]:
    """Resolve placeholders and filter optional EPICs by condition."""
    result = []
    for epic in epics:
        result.append(
            {
                "summary": resolve_placeholders(epic["summary"], params),
                "description": resolve_placeholders(epic["description"], params),
            }
        )
    for opt in optional_epics:
        condition_key = opt.get("condition", "")
        if condition_key and params.get(condition_key):
            result.append(
                {
                    "summary": resolve_placeholders(opt["summary"], params),
                    "description": resolve_placeholders(opt["description"], params),
                }
            )
    return result


def write_artifact_files(
    epic_list: list[dict[str, str]],
    parent_feature: str,
    output_dir: Path,
    dry_run: bool,
) -> list[str]:
    """Write epic-creator compatible artifact files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    decomp_path = output_dir / f"{parent_feature}-decomposition.md"
    epic_count = len(epic_list)
    decomp_content = textwrap.dedent(f"""\
        ---
        parent_strat: "{parent_feature}"
        epic_count: {epic_count}
        critical_path_length: {epic_count}
        triage: "templated-variant"
        triage_rationale: "Accelerator variant lifecycle"
        ---

        ## Epic List

        | # | ID | Title | Type | Priority |
        |---|-----|-------|------|----------|
    """)
    for i, epic in enumerate(epic_list, 1):
        epic_id = f"{parent_feature}-E{i:03d}"
        decomp_content += f"| {i} | {epic_id} | {epic['summary']} | Implementation | P0 |\n"

    decomp_content += "\n## Dependency DAG\n\n```mermaid\ngraph LR\n"
    for i in range(1, epic_count + 1):
        epic_id = f"{parent_feature}-E{i:03d}"
        if i < epic_count:
            next_id = f"{parent_feature}-E{i + 1:03d}"
            decomp_content += f"    {epic_id} --> {next_id}\n"
        else:
            decomp_content += f"    {epic_id}\n"
    decomp_content += "```\n"

    if dry_run:
        print(f"[dry-run] Would write: {decomp_path}")
        print(decomp_content)
    else:
        decomp_path.write_text(decomp_content, encoding="utf-8")
        created.append(str(decomp_path))

    for i, epic in enumerate(epic_list, 1):
        epic_id = f"{parent_feature}-E{i:03d}"
        deps = [f"{parent_feature}-E{i - 1:03d}"] if i > 1 else []
        deps_yaml = "\n".join(f'  - "{d}"' for d in deps) if deps else "[]"

        content = textwrap.dedent(f"""\
            ---
            epic_id: "{epic_id}"
            parent_strat: "{parent_feature}"
            component: "AIPCC Ecosystems"
            team: ""
            type: "Implementation"
            implementation_type: null
            priority: "P0"
            dependencies: {deps_yaml}
            ai_signals:
              change_specificity: 1
              pattern_precedent: 1
              adapter_pattern: 0
              existing_foundation: 1
              open_questions: 0
              external_dependency: 0
              human_process_gates: 0
              repo_access: 1
              architecture_claims: 0
            ---

            # {epic["summary"]}

            ## Description

            {epic["description"]}

            ## Acceptance Criteria

            - [ ] Implementation complete and tested
            - [ ] Changes merged to target branch
        """)

        epic_path = output_dir / f"{epic_id}.md"
        if dry_run:
            print(f"[dry-run] Would write: {epic_path}")
        else:
            epic_path.write_text(content, encoding="utf-8")
            created.append(str(epic_path))

    return created


def write_jira_files(
    epic_list: list[dict[str, str]],
    parent_feature: str,
    jira_config: dict,
    output_dir: Path,
    dry_run: bool,
    labels: str | None = None,
    due_date: str | None = None,
) -> list[str]:
    """Write Jira JSON files for acli workitem create."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    for i, epic in enumerate(epic_list, 1):
        additional: dict = {
            "components": [{"name": jira_config["component"]}],
            "parent": {"key": parent_feature},
            "security": {"name": jira_config["security"]},
        }
        if labels:
            additional["labels"] = [labels]
        if due_date:
            additional["duedate"] = due_date

        payload = {
            "projectKey": jira_config["project"],
            "type": jira_config["type"],
            "summary": epic["summary"],
            "description": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": epic["description"]},
                        ],
                    }
                ],
            },
            "additionalAttributes": additional,
        }

        filename = f"{parent_feature}-E{i:03d}-jira.json"
        jira_path = output_dir / filename
        if dry_run:
            print(f"[dry-run] Would write: {jira_path}")
            print(json.dumps(payload, indent=2))
        else:
            jira_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            created.append(str(jira_path))

    return created


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate EPIC decomposition for accelerator variant releases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--templates",
        type=Path,
        required=True,
        help="Path to epic-templates.yaml",
    )
    parser.add_argument("--accelerator", required=True, help="Accelerator identifier")
    parser.add_argument("--accel-version", required=True, help="Display name with version")
    parser.add_argument("--variant", required=True, help="Base image identifier")
    parser.add_argument("--release", required=True, help="Target release milestone")
    parser.add_argument("--parent-feature", required=True, help="Parent feature key")
    parser.add_argument("--hardware-type", required=True, help="Hardware type for QE")
    parser.add_argument("--torch-version", default=None, help="PyTorch version")
    parser.add_argument("--vllm-version", default=None, help="vLLM version")
    parser.add_argument("--sendnn-constraints", default=None, help="Spyre post-release constraints")
    parser.add_argument("--labels", default=None, help="Jira label to apply")
    parser.add_argument("--due-date", default=None, help="EPIC due date (YYYY-MM-DD)")
    parser.add_argument(
        "--mode",
        choices=["artifact", "jira", "both"],
        default="both",
        help="Output mode (default: both)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/epic-tasks"),
        help="Output directory (default: artifacts/epic-tasks)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = parse_args(argv)

    if not args.templates.exists():
        print(f"Error: templates file not found: {args.templates}", file=sys.stderr)
        sys.exit(1)

    if not re.match(r"^[A-Z]+-\d+$", args.parent_feature):
        print(
            f"Error: invalid parent-feature key '{args.parent_feature}' "
            f"(expected format: PROJ-12345)",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.due_date:
        try:
            datetime.date.fromisoformat(args.due_date)
        except ValueError:
            print(
                f"Error: --due-date must be YYYY-MM-DD, got '{args.due_date}'",
                file=sys.stderr,
            )
            sys.exit(1)

    args.accelerator = args.accelerator.lower()

    config = load_templates(args.templates)

    if args.accelerator != "spyre":
        if not args.torch_version or not args.vllm_version:
            print(
                f"Error: --torch-version and --vllm-version are required "
                f"for accelerator '{args.accelerator}'",
                file=sys.stderr,
            )
            sys.exit(1)

    template_name, epics, optional_epics = select_template(
        config, args.accelerator, args.accel_version
    )

    params = build_params(args)
    epic_list = build_epic_list(epics, optional_epics, params)

    print(f"Template: {template_name}")
    print(f"EPICs to generate: {len(epic_list)}")
    for i, epic in enumerate(epic_list, 1):
        print(f"  {i}. {epic['summary']}")
    print()

    created_files: list[str] = []

    if args.mode in ("artifact", "both"):
        files = write_artifact_files(epic_list, args.parent_feature, args.output_dir, args.dry_run)
        created_files.extend(files)

    jira_dir = args.output_dir / "jira"
    if args.mode in ("jira", "both"):
        files = write_jira_files(
            epic_list,
            args.parent_feature,
            config["jira"],
            jira_dir,
            args.dry_run,
            labels=args.labels,
            due_date=args.due_date,
        )
        created_files.extend(files)

    if not args.dry_run and created_files:
        print(f"\nCreated {len(created_files)} files:")
        for f in created_files:
            print(f"  {f}")

    if args.mode in ("jira", "both") and not args.dry_run:
        print("\nTo create Jira tickets, run:")
        for f in created_files:
            if f.endswith("-jira.json"):
                print(f"  acli jira workitem create --from-json {f}")


if __name__ == "__main__":
    main()
