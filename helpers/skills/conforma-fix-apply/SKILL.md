---
name: conforma-fix-apply
description: Apply code or configuration fixes to resolve a Conforma violation. Handles Dockerfile modifications, pipeline YAML updates, and cluster resource changes. Use when a violation has been analyzed and a fix strategy is identified.
allowed-tools: Bash(python3:*,git:*,kubectl:*,oc:*)
---

# Conforma Fix Apply

Applies code and/or configuration fixes to address the root cause of a Conforma violation.

## Fix Types

- **Code changes**: Dockerfile modifications, adding/removing pipeline tasks, source code fixes
- **Cluster/config changes**: Tekton pipeline YAML updates, prefetch-dependencies config, secrets, ConfigMaps via `oc`/`kubectl`

## Prerequisites

- `investigation.violation_analyze` must be `completed` in the handover
- `git`, `kubectl`/`oc` CLIs available and authenticated

## Important: Human-in-the-Loop

The agent **MUST** present the proposed fix and get engineer approval before applying.

## Instructions

```bash
python3 scripts/apply_fix.py --handover <handover.json> [--output <output.json>]
```

### Arguments

- `--handover` (required): path to handover JSON with completed `investigation.violation_analyze`
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Output

Updates the handover `investigation.fix_apply` section with:
- `fix_type`: `"code_change"` or `"cluster_config"`
- `description`: what was changed and why
- `files_modified`: list of file paths or k8s resource names
- `requires_rebuild`: whether a pipeline rerun is needed

## Error Handling

- If the fix cannot be applied, set `investigation.fix_apply.status` to `"failed"` with details
- If `investigation.violation_analyze` is not completed, exit with a prerequisite error
