---
name: conforma-report-fetch
description: Fetch a Conforma (Enterprise Contract) verification report from the Tekton Results API for a given namespace and pipeline run. Use when the user needs to retrieve or inspect a Conforma report from Konflux.
allowed-tools: Bash(python3:*,kubectl:*,oc:*)
---

# Conforma Report Fetch

Fetches a Conforma verification report from the Tekton Results API.

## Prerequisites

- `kubectl` or `oc` CLI authenticated to the target cluster
- Access to the Tekton Results API endpoint
- Namespace where the PipelineRun exists

## Instructions

Run the fetch script to retrieve a report:

```bash
python3 scripts/fetch_report.py --namespace <namespace> [--pipeline-run <name>] [--component <name>]
```

### Arguments

- `--namespace` (required): the Kubernetes namespace
- `--pipeline-run` (optional): specific PipelineRun name; if omitted, fetches the latest
- `--component` (optional): filter to a specific component
- `--handover` (optional): path to an existing handover JSON to update
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Output

Writes a handover JSON document with `metadata` and `report_fetch` sections populated.

### Important

Logs on the Konflux cluster are pruned aggressively after PipelineRun completion. This skill **must** use the Tekton Results API, not `kubectl logs`.

## Error Handling

- If the namespace is unreachable, report the error in the handover `report_fetch.error` field
- If no matching PipelineRun is found, set `report_fetch.status` to `"failed"` with a descriptive error
