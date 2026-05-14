---
name: conforma-doc-update
description: Document verified solutions back into per-violation YAML files so future investigations find them automatically. Appends resolved cases to existing files or creates new violation YAML files. Use after a successful rerun confirms a fix worked.
allowed-tools: Bash(python3:*,git:*)
---

# Conforma Doc Update

Documents verified solutions into the YAML violation files. This is the feedback loop that makes the system self-improving.

## Two Modes

- **Known violation** (YAML file exists): appends a new entry to `resolved_cases` -- purely deterministic, no LLM needed
- **New unknown violation** (no YAML file): LLM structures a new YAML file from the investigation data following the standard schema; engineer reviews via git MR before merge

## Prerequisites

- `investigation.rerun` must be `completed` with `result: "pass"`

## Instructions

```bash
python3 scripts/update_docs.py --handover <handover.json> [--output <output.json>]
```

### Arguments

- `--handover` (required): path to handover JSON with a successful rerun
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Output

Updates the handover `investigation.doc_update` section and writes to `references/violations/{violation_code}.yaml` via git.

## Error Handling

- If `investigation.rerun` did not pass, exit with a prerequisite error
- If git operations fail, set status to `"failed"` with details
