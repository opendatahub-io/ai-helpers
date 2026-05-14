---
name: conforma-violation-parse
description: Parse a Conforma report YAML into structured violation JSON. Extracts components, violation codes, rules, messages, and severity. Use when processing a fetched Conforma report into actionable violation data.
allowed-tools: Bash(python3:*)
---

# Conforma Violation Parse

Parses a raw Conforma report YAML into structured violation JSON. This is the critical handoff point -- everything downstream depends on this structured output.

## Instructions

Run the parser against a fetched report:

```bash
python3 scripts/parse_violations.py --handover <handover.json> [--output <output.json>]
```

### Arguments

- `--handover` (required): path to the handover JSON containing `report_fetch.raw_report_path`
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Prerequisites

The `report_fetch` section in the handover must have `status: "completed"`.

### Output

Updates the handover with a `violation_parse` section containing:

```json
{
  "violation_parse": {
    "status": "completed",
    "violations": [
      {
        "component": "component-x",
        "container_image": "quay.io/org/component-x@sha256:abc...",
        "rule": "attestation_task.sbom_task_present",
        "violation_code": "missing_sbom",
        "msg": "SBOM not found for component",
        "severity": "failure"
      }
    ],
    "violation_count": 1
  }
}
```

## Error Handling

- If the report YAML is malformed, set `violation_parse.status` to `"failed"` with the parse error
- If `report_fetch` is not completed, exit with an error describing the missing prerequisite
