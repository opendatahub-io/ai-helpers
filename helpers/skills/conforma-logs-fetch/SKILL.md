---
name: conforma-logs-fetch
description: Fetch component build logs from the Tekton Results API for a specific violation under investigation. Use when the user needs build logs to diagnose a Conforma violation.
allowed-tools: Bash(python3:*,kubectl:*,oc:*)
---

# Conforma Logs Fetch

Fetches component build logs from the Tekton Results API for the violation currently under investigation.

## Prerequisites

- `kubectl` or `oc` CLI authenticated to the target cluster
- Access to the Tekton Results API endpoint
- Handover with `violation_parse` completed and an `investigation.violation` selected

## Instructions

```bash
python3 scripts/fetch_logs.py --handover <handover.json> [--output <output.json>]
```

### Arguments

- `--handover` (required): path to handover JSON with `investigation.violation` populated
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Output

Updates the handover `investigation.logs_fetch` section with filtered log text.

### Important

Logs on the Konflux cluster are pruned aggressively. This skill **must** use the Tekton Results API, not `kubectl logs`.

## Error Handling

- If the component's logs are unavailable, set `investigation.logs_fetch.status` to `"failed"` with a descriptive error
- If `violation_parse` or `investigation.violation` prerequisites are not met, exit with an error
