---
name: conforma-rerun
description: Trigger a pipeline rebuild and verify the new Conforma verification result. Use after applying a fix or creating an exception to confirm the violation is resolved.
allowed-tools: Bash(python3:*,kubectl:*,oc:*)
---

# Conforma Rerun

Triggers a rebuild/pipeline run and fetches the new Conforma verification result to confirm the fix or exception worked.

## Prerequisites

- Either `investigation.fix_apply` OR `investigation.exception_create` must be `completed`
- `kubectl` or `oc` CLI authenticated to the target cluster

## Instructions

```bash
python3 scripts/rerun_conforma.py --handover <handover.json> [--output <output.json>]
```

### Arguments

- `--handover` (required): path to handover JSON with a completed fix or exception
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Output

Updates the handover `investigation.rerun` section with:
- `new_pipeline_run`: the new PipelineRun name
- `result`: `"pass"`, `"fail"`, or `"pending"`
- `new_violations`: violation objects if still failing

### Rerun Loop

If the rerun fails (violation still present), the handover captures new violations so the agent can loop back to re-analyze.

## Error Handling

- If neither fix_apply nor exception_create is completed, exit with a prerequisite error
- If the rebuild fails to start, set status to `"failed"` with details
