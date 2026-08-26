---
name: triage-bug-readiness
description: Use when assessing a Jira bug ticket for AI autofix readiness. Produces a structured JSON verdict (ready/needs_info/not_fixable) based on a three-gate rubric. Designed for CI pipeline use with the jira-triage orchestrator.
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

If none of these files exist, explore the repository from scratch: check `go.mod` or `package.json` for the language/framework, list top-level directories, and read any contributing guides.

## Step 3: Explore the actual code

**Prerequisite**: This step requires a cloned repository. The orchestrator only invokes the agent when a repo URL was found in the ticket, so a clone should always be available. If for any reason no repo is present in the working directory, set `repo_readiness` fields to `false` with a note and proceed directly to Step 4.

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

See `references/rubric-and-schema.md` for the full gate rubric (pass/fail criteria with examples), verdict logic, JSON schema, field requirements, and actionable feedback templates.

**Gate summary:**

- **Gate 1 -- Can the Agent Start?** Repo URL exists and ticket states what is broken (not just "it's broken").
- **Gate 2 -- Can the Agent Find and Fix It?** Code is locatable (file paths, error messages, component names) and correct behavior is unambiguous.
- **Gate 3 -- Should an Agent Fix This?** Not blocked by design decisions, infrastructure, external deps, runtime-only diagnosis, performance tuning, or non-code fixes.

**Verdict logic:** Gate 1 fail -> `needs_info`; Gate 3 fail -> `not_fixable`; Gate 2 pass -> `ready`; else -> `needs_info`. Prefer `ready` with `"confidence": "low"` over `not_fixable` when uncertain.

## Step 5: Write structured verdict to file

Write the verdict as JSON to `.triage-verdict.json` in the repository root. Use the Write tool to create this file. Do NOT just print it to stdout. See `references/rubric-and-schema.md` for the full JSON schema and field requirements.

## Step 6: Generate actionable feedback

For `needs_info` verdicts, `message_to_opener` must reference the specific failed gate and tell the opener exactly what to provide. For `not_fixable`, explain the Gate 3 category and suggest human intervention. For `ready`, use an empty string. See `references/rubric-and-schema.md` for message templates.

## Example

```
/triage-bug-readiness AIPCC-1234
```

## Gotchas

- **Bias toward ready**: A wasted autofix cycle is cheaper than a missed fix. When on the fence, classify as `ready` with `"confidence": "low"` rather than `not_fixable`.
- **Cross-repo is not systemic**: Fixes spanning multiple repos in the same GitHub/GitLab org are still `ready`, not `systemic_architectural`. Only use `not_fixable` when the dependency is genuinely outside the team's control.
- **No repo clone is not a hard stop**: If no repo is present in the working directory, set `repo_readiness` fields to `false` with a note and proceed to Step 4 -- do not abort the entire assessment.
