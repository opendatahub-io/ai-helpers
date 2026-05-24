---
name: conforma-exception-create
description: Create a GitLab merge request to add a Conforma exception or waiver policy when a violation cannot or should not be fixed. Use when an analyzed violation requires a policy exemption rather than a code fix.
allowed-tools: Bash(python3:*,glab:*,git:*)
---

# Conforma Exception Create

Creates a GitLab merge request to add a Conforma exception/waiver policy. This exempts a component from a policy rather than fixing the root cause.

## Important: Human-in-the-Loop

Exception MRs bypass policy enforcement. Engineer approval is **MANDATORY** before creation.

## Modes

This skill supports two modes. The script validates all inputs in both modes — if it reports errors, relay them to the user and re-run with corrected input.

### Pipeline mode (with handover)

Used when an upstream agent (e.g. `conforma-troubleshooter`) has already produced a handover document with a completed violation analysis.

```bash
python3 scripts/create_exception.py --handover <handover.json> [--output <output.json>]
```

Prerequisites:
- `investigation.violation_analyze` must be `completed` in the handover
- `investigation.violation.rule` must be present
- `glab` CLI installed and authenticated

### Standalone mode (user-provided details)

Used when an engineer invokes this skill directly without a prior pipeline run. Before running the script, ask the user for the required details listed below.

```bash
python3 scripts/create_exception.py \
  --container-image <image-ref> \
  --rule <policy-rule> \
  --effective-until <YYYY-MM-DD> \
  --jira-url <ticket-url> \
  --justification <reason> \
  [--component <name>] \
  [--policy-repo <gitlab-project-path>] \
  [--output <output.json>]
```

Required information to collect from the user:

| Detail | Flag | Example |
|--------|------|---------|
| Container image being exempted | `--container-image` | `quay.io/org/image@sha256:abc...` |
| Policy rule to exempt | `--rule` | `attestation_task.sbom_task_present` |
| Exception expiry date | `--effective-until` | `2026-09-30` |
| JIRA ticket URL for the exception | `--jira-url` | `https://issues.redhat.com/browse/RHOAIENG-1234` |
| Why the exception is needed | `--justification` | `Docs-only repo, no container image produced` |

Optional:

| Detail | Flag | Default |
|--------|------|---------|
| Component name | `--component` | `unknown` |
| GitLab exception policy repo | `--policy-repo` | *(none)* |

## Output

Updates the handover `investigation.exception_create` section with:
- `mr_url`: GitLab MR URL
- `exception_policy`: the policy rule being exempted
- `justification`: why the exception is needed

## Reference Documentation

Upstream docs relevant to exception creation are listed in
`helpers/skills/conforma-doc-search/references/external-references.yaml`.
Fetch the URLs at runtime when you need details on the exception format,
volatile config fields, or the Konflux approval process.

## Error Handling

The script validates inputs and exits with a non-zero code on failure. Common errors:
- Missing required arguments (standalone mode)
- `--effective-until` is not a valid future date
- `investigation.violation_analyze` not completed (pipeline mode)
- `glab` not authenticated — exit with setup instructions
- MR creation failure — status set to `"failed"` with details

If the script reports a validation error, relay the message to the user and re-run after the issue is corrected.
