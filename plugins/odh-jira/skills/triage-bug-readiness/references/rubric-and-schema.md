# Triage Bug Readiness: Detailed Rubric and Verdict Schema

## Gate Details

### Gate 1: Can the Agent Start? (minimum to proceed)

**Target repository:**

The orchestrator verifies that a repo URL exists before invoking this skill. Record the URL from the ticket in `gate1.repo_url.value` and set `gate1.repo_url.pass: true`.

**What is broken:**

- PASS: The ticket states what goes wrong, even briefly. Examples of sufficient descriptions:
  - "divide() returns the product instead of the quotient"
  - "The dashboard returns 403 after upgrading to 2.25"
  - "RBAC error: SA lacks permission to update scheduledsparkapplications/finalizers"
- FAIL: The ticket is vague or only states a desire without identifying a problem:
  - "Dashboard is broken"
  - "Please fix the model serving component"
  - "Something is wrong with authentication"

### Gate 2: Can the Agent Find and Fix It?

**Code locatability** -- Can the agent find where the bug lives?

- PASS: The ticket provides enough signal to locate the relevant code through exploration:
  - Specific file/function names
  - An error message or log output greppable in the codebase
  - A CRD field name, API endpoint, or UI element name
  - A component name + feature area that narrows to a few directories
- FAIL: The description is too vague for even code exploration to narrow down.

**Fix direction** -- Does the agent know what "correct" looks like?

- PASS: The correct behavior is stated or unambiguous from context:
  - A crash/panic should not crash
  - A 500/403 error should return the expected response
  - "Returns product instead of quotient" -- should return quotient
  - "Config option works on page A but not page B" -- should work on both
- FAIL: The "correct" behavior is genuinely ambiguous and requires a human design decision:
  - "The UI should be better"
  - "Model serving should be faster"
  - "The error message is confusing"

Both code locatability and fix direction must PASS for Gate 2 to pass.

### Gate 3: Should an Agent Fix This? (scope and feasibility)

Even with perfect information, some bugs are not appropriate for automated fixing:

- **requires_design_decisions**: The "correct" behavior is subjective (UX preferences, API design choices)
- **requires_infrastructure**: Hardware-dependent, cloud service issues, CI/release engineering problems
- **systemic_architectural**: Fix requires changes in a truly external dependency (different organization, closed-source, or requires a release/publish process the agent cannot trigger)
- **needs_runtime_investigation**: Can only be diagnosed on a live cluster with specific state
- **performance**: Requires profiling, benchmarking, and potentially architectural changes
- **non_code_fix**: The resolution is not a code change -- e.g., KCS article update, documentation fix, Jira configuration, or infra/config-only change that the autofix agent cannot make

**Cross-repo within the same organization:** If the fix requires changes in a different repository but that repository belongs to the same GitHub/GitLab organization (e.g., both repos are under `opendatahub-io`), this is NOT `systemic_architectural`. Classify as **ready** and note in `gate3.note` that the fix spans multiple repos within the org. The autofix agent can be given access to sibling repos in the same organization. Only classify as `not_fixable` with `systemic_architectural` when the upstream dependency is genuinely outside the team's control.

**Blocked or dependent bugs:** If a ticket has a "blocked by" link or depends on an external fix, consider whether a workaround exists in the target repo (compatibility shim, version pin, fallback path, feature gate). If a viable workaround exists, classify as `ready` with `"confidence": "medium"` and describe the workaround approach in `gate3.note`. Only classify as `not_fixable` if there is truly no interim mitigation possible within the target repo.

## Verdict Logic

```text
if Gate 1 fails:
    verdict = "needs_info"
elif Gate 3 fails:
    verdict = "not_fixable"
elif Gate 2 passes:
    verdict = "ready"
else:
    verdict = "needs_info"
```

## Verdict JSON Schema

Write the verdict as JSON to `.triage-verdict.json` in the repository root. Use the Write tool to create this file. Do NOT just print it to stdout.

```json
{
  "verdict": "ready | needs_info | not_fixable",
  "confidence": "high | medium | low",
  "gate1": {
    "repo_url": {
      "pass": true,
      "value": "https://github.com/org/repo",
      "note": "Found in ticket description"
    },
    "bug_description": {
      "pass": true,
      "note": "Clear description of incorrect behavior"
    }
  },
  "gate2": {
    "code_locatability": {
      "pass": true,
      "note": "Function confirmed in codebase at expected path"
    },
    "fix_direction": {
      "pass": true,
      "note": "Correct behavior is unambiguous"
    }
  },
  "gate3": {
    "pass": true,
    "not_fixable_reason": null,
    "note": "Bounded scope, single-repo fix",
    "cross_repo": null
  },
  "repo_readiness": {
    "has_agent_docs": false,
    "has_build_targets": true,
    "has_lint_config": true,
    "note": "Has Makefile with lint/test/build targets but no AGENTS.md"
  },
  "risk_factors": ["area under active refactor", "shared code with wide blast radius"],
  "missing": ["list of specific missing items, if any"],
  "message_to_opener": "",
  "reasoning": "Brief explanation of the overall assessment."
}
```

### Field Requirements

- `verdict`: One of `"ready"`, `"needs_info"`, `"not_fixable"`.
- `confidence`: Your confidence in the verdict. `"high"` = clear-cut. `"medium"` = reasonable but some uncertainty. `"low"` = borderline call.
- `gate1`, `gate2`, `gate3`: Assessment of each gate with pass/fail and notes.
- `gate1.repo_url.value`: The repo URL from the ticket. Always present (the orchestrator pre-filters tickets without a URL).
- `gate3.not_fixable_reason`: One of `"requires_design_decisions"`, `"requires_infrastructure"`, `"systemic_architectural"`, `"needs_runtime_investigation"`, `"performance"`, `"non_code_fix"`, or `null` if Gate 3 passes.
- `gate3.cross_repo`: If the fix spans multiple repos within the same org, list the additional repo URLs here (e.g., `["https://github.com/opendatahub-io/elyra"]`). Set to `null` for single-repo fixes or truly external dependencies.
- `repo_readiness`: Object describing the repo's readiness for automated fixing. Fields: `has_agent_docs` (bool -- `AGENTS.md`, `CLAUDE.md`, or `CONTRIBUTING.md` exists), `has_build_targets` (bool -- `Makefile` or equivalent has `build`/`test`/`lint` targets), `has_lint_config` (bool -- `.golangci.yml`, `.eslintrc`, `pyproject.toml [tool.ruff]`, etc.), `note` (string -- brief summary).
- `risk_factors`: Array of strings identifying factors that increase the difficulty or blast radius of the fix (e.g., `"no lint config"`, `"area under active refactor"`, `"shared code with wide blast radius"`, `"no test coverage near bug area"`). Empty array if no notable risks.
- `missing`: List of specific things missing from the ticket (empty array if verdict is `"ready"` or `"not_fixable"`).
- `message_to_opener`: The message to post on the Jira ticket. Required for `"needs_info"` and `"not_fixable"` verdicts. Must be specific -- reference the exact gate that failed and tell the opener exactly what to provide. Empty string for `"ready"` verdicts.
- `reasoning`: Brief (1-3 sentence) explanation of the verdict.

## Actionable Feedback (Step 6)

For `needs_info` verdicts, the `message_to_opener` MUST be specific to what is actually missing. Do NOT produce generic "please add more info" messages. Structure the message as:

```markdown
**Needed** (without these, the autofix agent cannot proceed):

1. [Specific missing item referencing the failed gate]

**Helpful** (these make the fix faster and more accurate, but the agent can work without them):

- [Optional items that would speed up the fix]
```

Always end the message with: "Please update the ticket, then remove the `jira-triage-needs-info` label to re-trigger assessment."

For `not_fixable` verdicts, explain clearly why the bug is not suitable for automated fixing, referencing the specific Gate 3 category. Suggest what kind of human intervention is needed (e.g., "A release engineer should investigate" or "This requires a design discussion to determine the correct behavior").

For `ready` verdicts, `message_to_opener` should be an empty string.
