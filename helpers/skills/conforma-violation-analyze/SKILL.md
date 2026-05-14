---
name: conforma-violation-analyze
description: Analyze a Conforma violation to determine root cause, suggest a fix, and assign a confidence level. Uses violation data, component build logs, and per-violation YAML documentation as context. Use when a violation has been fetched, parsed, and its logs and docs retrieved.
---

# Conforma Violation Analyze

LLM-powered root-cause analysis for a single Conforma violation.

## Context (Priority Order)

1. `investigation.violation` -- the specific violation being analyzed (what went wrong)
2. `investigation.logs_fetch.logs` -- component build logs (what actually happened)
3. `investigation.doc_search.violation_data` -- structured YAML for this violation (known solutions, fix steps, symptoms, resolved cases)
4. `violation_parse.violations` -- other violations in the same report (useful for spotting patterns, e.g., "3 components all failing the same policy suggests a pipeline-level issue")

## Prerequisites

- `investigation.logs_fetch` must be `completed`
- `investigation.doc_search` must be `completed`

## Instructions

Given the violation, logs, and documentation context from the handover:

1. **Identify the root cause** from the evidence in the logs and the known patterns in the violation YAML
2. **Suggest a fix** -- be specific (which file to change, which command to run, which config to update)
3. **Assign confidence**:
   - `high`: matches a known pattern with resolved cases
   - `medium`: matches symptoms but no exact resolved case
   - `low`: no documentation match, analysis is based solely on logs
4. **List evidence**: cite specific log lines and doc sections that support the analysis

## Output Format

Write the analysis to `investigation.violation_analyze` in the handover:

```json
{
  "status": "completed",
  "root_cause": "The generate-sbom task is missing from .tekton/push.yaml",
  "suggested_fix": "Add generate-sbom task after build-container in .tekton/push.yaml",
  "confidence": "high",
  "evidence": [
    "Log line 142: 'no SBOM artifact found'",
    "Violation YAML: fix_steps[0] says 'Check if generate-sbom task is present'"
  ]
}
```

## Decision: Fix vs Exception

Based on the analysis, recommend one of:
- **Fix** (`conforma-fix-apply`): the violation has a concrete fix
- **Exception** (`conforma-exception-create`): the violation cannot or should not be fixed (e.g., component genuinely doesn't produce an image)

State the recommendation clearly so the agent or engineer can proceed.
