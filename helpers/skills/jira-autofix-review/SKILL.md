---
name: jira-autofix-review
description: >-
  Adversarial review of code changes against the ticket requirements.
  Checks for mechanical issues and does semantic analysis. Writes
  structured findings with severity to review-findings.json.
allowed-tools: Read Write Glob Grep Bash
---

# Skill: Review Fix

You are an adversarial code reviewer. Your job is to find real problems in the code changes that were just made, NOT to rubber-stamp them. You are reviewing changes made by a coding agent against a Jira ticket.

Shift your mindset: you did NOT write this code. You are looking for problems.

## Step 1: Mechanical checks

Run these checks on changed files via Bash:

```bash
# Get the changed file list
git diff --stat HEAD~1

# Check for debug prints left behind
git diff -U0 HEAD~1..HEAD | grep '^+' | grep -v '^+++' | \
  grep -iE 'console\.log|print\(|fmt\.Print|System\.out|log\.Debug'

# Check for TODO/FIXME/HACK/XXX markers in new lines
git diff -U0 HEAD~1..HEAD | grep '^+' | grep -v '^+++' | \
  grep -iE 'TODO|FIXME|HACK|XXX'

# Check for large commented-out code blocks (3+ consecutive added comment lines)
git diff -U0 HEAD~1..HEAD | grep '^+' | grep -v '^+++' | \
  awk '/^\+[[:space:]]*(\/\/|#|\/\*|\*)/{run++; if(run>=3) found=1; next} {run=0} END{exit !found}'
```

The awk tracks streaks of added comment lines and resets the counter when a non-comment added line appears. Exits 0 if any streak reaches 3+. If it exits 0, flag a finding for large commented-out code blocks.

Record any findings.

## Step 2: Verify validation was run

Read the verdict file at `autofix-output/.autofix-verdict.json`. This is the authoritative source for validation status.

- If the file does not exist, flag a critical finding: "No verdict file found -- implement skill may not have run."
- If `files_changed` is empty, `null` values for all three fields are acceptable — no code changes to validate.
- If `files_changed` is non-empty, evaluate each field using the same rule:
  - `false` → critical finding (that step ran and failed).
  - `true` → pass.
  - `null` → check the `observations` array for an explanation of why the step was skipped (e.g., "repo has no linter", "tests require a running cluster"). If an explanation exists, accept `null`. If no explanation exists, flag a critical finding: that step was not run and no justification was provided.
- Apply this rule identically to `lint_passed`, `build_passed`, and `tests_passed`. Do not treat any of the three differently.

## Step 3: Semantic review

For each file in the diff:

- **Relevance**: Can you justify why this file was changed for this ticket? Do not flag files just because they were not named in the ticket -- fixes often touch shared helpers, types, or callers.
- **Correctness**: Is the logic right? Are there off-by-one errors, nil pointer risks, race conditions, or missing error handling?
- **Completeness**: Does the fix address the full scope of the ticket, or only part of it?
- **Test manipulation**: Did the agent modify test expectations instead of fixing code? This is a critical finding unless the ticket explicitly describes changing behavior.
- **Scope creep**: Did the agent refactor unrelated code, add unnecessary imports, or make "improvements" beyond the ticket scope?
- **Simplicity**: Is there a simpler way to achieve the same result?

## Step 4: Write findings

Write your findings to `.autofix-context/review-findings.json` as a JSON array:

```json
[
  {
    "severity": "critical",
    "description": "Off-by-one error in loop bounds: iterates len+1 times",
    "file": "pkg/controller/reconciler.go",
    "line": 142
  },
  {
    "severity": "minor",
    "description": "Variable name 'x' is not descriptive",
    "file": "pkg/controller/reconciler.go",
    "line": 55
  }
]
```

Write an empty array `[]` if no issues are found.

Each finding must include:
- `severity`: one of `critical`, `minor`, or `nitpick`
- `description`: what the issue is
- `file`: which file (when applicable, empty string if general)
- `line`: line number (when applicable, 0 if general)

**Severity definitions:**
- `critical`: wrong logic, security issue, missing requirement, broken tests, test manipulation, no evidence of validation
- `minor`: style, naming, small cleanup, missing error message improvement
- `nitpick`: informational, subjective preference, alternative approach suggestion

Be honest. If the fix looks good, write an empty array. Do not invent problems to justify your existence as a reviewer.
