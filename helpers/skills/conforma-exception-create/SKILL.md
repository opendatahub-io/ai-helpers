---
name: conforma-exception-create
description: Create a GitLab merge request to add a Conforma exception or waiver policy when a violation cannot or should not be fixed. Use when an analyzed violation requires a policy exemption rather than a code fix.
allowed-tools: Bash(python3:*,glab:*,git:*)
---

# Conforma Exception Create

Creates a GitLab merge request to add a Conforma exception/waiver policy. This exempts a component from a policy rather than fixing the root cause.

## Prerequisites

- `investigation.violation_analyze` must be `completed` in the handover
- `glab` CLI installed and authenticated
- Access to the policy/exception repository

## Important: Human-in-the-Loop

Exception MRs bypass policy enforcement. Engineer approval is **MANDATORY** before creation.

## Instructions

```bash
python3 scripts/create_exception.py --handover <handover.json> [--output <output.json>]
```

### Arguments

- `--handover` (required): path to handover JSON with completed `investigation.violation_analyze`
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Output

Updates the handover `investigation.exception_create` section with:
- `mr_url`: GitLab MR URL
- `exception_policy`: the policy rule being exempted
- `justification`: why the exception is needed

## Error Handling

- If `glab` is not authenticated, exit with setup instructions
- If the exception MR creation fails, set status to `"failed"` with details
