---
name: triage-bug-readiness
description: Assess a Jira bug ticket for AI autofix readiness. Produces a structured JSON verdict (ready/needs_info/not_fixable) based on a three-gate rubric. Designed for CI pipeline use with the jira-triage orchestrator.
allowed-tools: Read Grep Glob Write
---

# Skill: Triage Bug Readiness

You are assessing a Jira bug ticket for AI autofix readiness. Your goal is to determine whether an automated coding agent (Claude Code) can successfully fix this bug given the information available. You will produce a structured JSON verdict written to a file.

## Step 1: Parse the ticket content

Read the ticket summary, description, and comments provided in the prompt. Extract:

- What the reporter claims is broken (the symptom)
- Where they believe the bug is (component, feature area, file paths)
- Any error messages, log output, or stack traces
- Any repo URLs mentioned (GitLab or GitHub)
- Steps to reproduce (if provided)
- Expected vs. actual behavior (if stated)

## Step 2: Orient via context files

Read the following files in order of priority. Stop reading deeper once you have a solid mental map of the repo structure:

1. `.triage-context/ARCHITECTURE.md` (if present) -- Pre-generated architecture overview. Focus on the component map, CRD list, and directory structure. Use this to plan where to look in the code.
2. `AGENTS.md` and/or `CLAUDE.md` (if present in repo root) -- The repo's own agent guidance, conventions, and critical rules. These are authoritative and take precedence over the architecture doc.
3. `README.md` -- Fallback orientation if neither of the above exists.
4. `.triage-context/component-repos.conf` (if present) -- Maps component names to repo URLs. Use this if the ticket references a component by name but you need to confirm the repo URL.

If none of these files exist, explore the repository from scratch: check `go.mod` or `package.json` for the language/framework, list top-level directories, and read any contributing guides.

## Step 3: Explore the actual code

**Prerequisite**: This step requires a known target repository. If Gate 1 fails because the repo is unknown or ambiguous (no URL found, component name is ambiguous), skip this step entirely -- record the Gate 1 failure in the verdict with rationale, set `repo_readiness` fields to `false` with a note explaining the repo could not be identified, and proceed directly to Step 4.

When a target repo is available, context files are a map, not the territory. Use `Grep`, `Glob`, and `Read` to:

- **Locate the code area** referenced by the bug description. Verify it exists at the expected path. If the ticket mentions a function, CRD field, API endpoint, or error message, search for it.
- **Confirm references are current** -- function names, API paths, CRD fields, or error messages in the ticket must match the actual codebase. Flag stale references.
- **Check for test coverage** -- Look for tests near the bug area (`*_test.go`, `*.test.ts`, `test_*.py`, etc.). Repos with tests near the bug area are much more likely to produce a good autofix.
- **Review recent git history** (if shell access is available) -- Run `git log --oneline -20 -- <path>` for the relevant code area. Recent refactors may explain the bug or indicate the area is actively changing. If shell access is not available, skip this sub-step.
- **Assess agent-readiness of the repo** -- Check for `AGENTS.md`, `CLAUDE.md`, or `CONTRIBUTING.md`. Also look for `Makefile` targets (`make lint`, `make test`, `make build`) and CI config (`.github/workflows/`, `.gitlab-ci.yml`). Repos with agent docs AND working build/test targets have significantly higher autofix success rates. Record what you find -- this feeds into the `repo_readiness` field in the verdict.
- **Check build/lint/test infrastructure** -- Read the first ~60 lines of `Makefile` (or equivalent) to see available targets. If there is no way to validate a fix (no linter, no tests, no build target), the autofix agent may produce untestable patches. Note this as a risk factor but do NOT fail the ticket on this alone.
- **Check cross-component impact** -- Does the bug area touch shared code (e.g., `pkg/`, `lib/`, `utils/`) used by multiple consumers? If so, the fix has wider blast radius.

## Step 4: Assess readiness using the rubric

The core question: "If the autofix agent were handed this ticket right now, would it produce a correct fix, or would it waste a cycle guessing wrong?"

**Calibration: prefer ready when uncertain.** A wasted autofix cycle (the agent tries and fails) is far cheaper than a false rejection (a fixable bug sits untouched). When you are on the fence between `"ready"` and `"not_fixable"`, choose `"ready"` with `"confidence": "low"`. Reserve `"not_fixable"` for cases where you are genuinely confident the agent cannot succeed. The same bias applies at Gate 2: if code locatability is uncertain but plausible, pass the gate with a note rather than failing it.

### Gate 1: Can the Agent Start? (minimum to proceed)

**Target repository:**

- PASS: A valid GitLab/GitHub repo URL is in the description or comments.
- INFERRED: No explicit URL, but the component name is unambiguous. Check `.triage-context/component-repos.conf` or the architecture doc. When inferred, note this in the verdict so the orchestrator can confirm it in the Jira comment.
- FAIL: No URL and the component is ambiguous or unknown.

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

**Cross-repo within the same organization:** If the fix requires changes in a different repository but that repository is also listed in `.triage-context/component-repos.conf` or belongs to the same GitHub/GitLab organization (e.g., both repos are under `opendatahub-io`), this is NOT `systemic_architectural`. Classify as **ready** and note in `gate3.note` that the fix spans multiple repos within the org. The autofix agent can be given access to sibling repos in the same organization. Only classify as `not_fixable` with `systemic_architectural` when the upstream dependency is genuinely outside the team's control.

**Blocked or dependent bugs:** If a ticket has a "blocked by" link or depends on an external fix, consider whether a workaround exists in the target repo (compatibility shim, version pin, fallback path, feature gate). If a viable workaround exists, classify as `ready` with `"confidence": "medium"` and describe the workaround approach in `gate3.note`. Only classify as `not_fixable` if there is truly no interim mitigation possible within the target repo.

### Verdict Logic

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

## Step 5: Write structured verdict to file

Write the verdict as JSON to `.triage-verdict.json` in the repository root. Use the Write tool to create this file. Do NOT just print it to stdout.

The JSON schema:

```json
{
  "verdict": "ready | needs_info | not_fixable",
  "confidence": "high | medium | low",
  "gate1": {
    "repo_url": {
      "pass": true,
      "inferred": false,
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

Field requirements:

- `verdict`: One of `"ready"`, `"needs_info"`, `"not_fixable"`.
- `confidence`: Your confidence in the verdict. `"high"` = clear-cut. `"medium"` = reasonable but some uncertainty. `"low"` = borderline call.
- `gate1`, `gate2`, `gate3`: Assessment of each gate with pass/fail and notes.
- `gate1.repo_url.inferred`: Set to `true` if you resolved the repo URL from a component name rather than an explicit URL in the ticket. The orchestrator will include a confirmation prompt in its Jira comment.
- `gate1.repo_url.value`: The repo URL (explicit or inferred). Leave empty string if unknown.
- `gate3.not_fixable_reason`: One of `"requires_design_decisions"`, `"requires_infrastructure"`, `"systemic_architectural"`, `"needs_runtime_investigation"`, `"performance"`, `"non_code_fix"`, or `null` if Gate 3 passes.
- `gate3.cross_repo`: If the fix spans multiple repos within the same org, list the additional repo URLs here (e.g., `["https://github.com/opendatahub-io/elyra"]`). Set to `null` for single-repo fixes or truly external dependencies.
- `repo_readiness`: Object describing the repo's readiness for automated fixing. Fields: `has_agent_docs` (bool -- `AGENTS.md`, `CLAUDE.md`, or `CONTRIBUTING.md` exists), `has_build_targets` (bool -- `Makefile` or equivalent has `build`/`test`/`lint` targets), `has_lint_config` (bool -- `.golangci.yml`, `.eslintrc`, `pyproject.toml [tool.ruff]`, etc.), `note` (string -- brief summary).
- `risk_factors`: Array of strings identifying factors that increase the difficulty or blast radius of the fix (e.g., `"no lint config"`, `"area under active refactor"`, `"shared code with wide blast radius"`, `"no test coverage near bug area"`). Empty array if no notable risks.
- `missing`: List of specific things missing from the ticket (empty array if verdict is `"ready"` or `"not_fixable"`).
- `message_to_opener`: The message to post on the Jira ticket. Required for `"needs_info"` and `"not_fixable"` verdicts. Must be specific -- reference the exact gate that failed and tell the opener exactly what to provide. Empty string for `"ready"` verdicts.
- `reasoning`: Brief (1-3 sentence) explanation of the verdict.

## Step 6: Generate actionable feedback

For `needs_info` verdicts, the `message_to_opener` MUST be specific to what is actually missing. Do NOT produce generic "please add more info" messages. Structure the message as:

```markdown
**Needed** (without these, the autofix agent cannot proceed):

1. [Specific missing item referencing the failed gate]

**Helpful** (these make the fix faster and more accurate, but the agent can work without them):

- [Optional items that would speed up the fix]
```

Always end the message with: "Please update the ticket, then remove the `jira-triage-needs-info` label to re-trigger assessment."

For `not_fixable` verdicts, explain clearly why the bug is not suitable for automated fixing, referencing the specific Gate 3 category. Suggest what kind of human intervention is needed (e.g., "A release engineer should investigate" or "This requires a design discussion to determine the correct behavior").

For `ready` verdicts, `message_to_opener` should be an empty string. Any advisory notes (e.g., "repo URL was inferred") are handled by the orchestrator.
