---
name: jira-autofix-review
description: >-
  Use when reviewing code changes made by the implement skill against
  the ticket requirements. Checks for mechanical issues and does semantic
  analysis. Writes structured findings with severity to
  .autofix-context/review-findings.json.
allowed-tools: Read Write Glob Grep Bash
---

# Review Fix

Review the code changes made by the implement skill against the Jira ticket requirements. Look for real problems -- do not rubber-stamp. Treat the diff as code written by someone else and focus on finding issues.

## Step 1: Mechanical checks

Determine the changed file list, then run checks scoped to those files:

```bash
# Get changed files from the verdict (authoritative source).
# Exit code 0 = files list obtained (may be empty for no-code-change verdicts).
# Exit code 1 = verdict missing or unreadable, use git fallback.
VERDICT_READ=true
FILES=()
while IFS= read -r f; do
  [[ -n "$f" ]] && FILES+=("$f")
done < <(python3 -c "
import json, sys
try:
    v = json.load(open('autofix-output/.autofix-verdict.json'))
    files = v.get('files_changed')
    if files is None or not isinstance(files, list):
        sys.exit(1)
    for f in files:
        if not isinstance(f, str):
            sys.exit(1)
        print(f)
except Exception:
    sys.exit(1)
" 2>/dev/null) || VERDICT_READ=false

# Fallback: extract from git if verdict was unreadable
if [[ "$VERDICT_READ" == false ]]; then
  while IFS= read -r f; do
    [[ -n "$f" ]] && FILES+=("$f")
  done < <(git diff --name-only HEAD~1..HEAD 2>/dev/null)
fi

# Run mechanical checks only if there are files to check
if [[ ${#FILES[@]} -gt 0 ]]; then
  # Check for debug prints left behind
  git diff -U0 HEAD~1..HEAD -- "${FILES[@]}" | grep '^+' | grep -v '^+++' | \
    grep -iE 'console\.log|print\(|fmt\.Print|System\.out|log\.Debug'

  # Check for TODO/FIXME/HACK/XXX markers in new lines
  git diff -U0 HEAD~1..HEAD -- "${FILES[@]}" | grep '^+' | grep -v '^+++' | \
    grep -iE 'TODO|FIXME|HACK|XXX'

  # Check for large commented-out code blocks (3+ consecutive added comment lines)
  git diff -U0 HEAD~1..HEAD -- "${FILES[@]}" | grep '^+' | grep -v '^+++' | \
    awk '/^\+[[:space:]]*(\/\/|#|\/\*|\*)/{run++; if(run>=3) found=1; next} {run=0} END{exit !found}'
fi
```

The `FILES` array is built from the verdict's `files_changed` (one entry per line to handle paths with spaces). If the verdict is unreadable, the fallback uses `git diff --name-only HEAD~1`. If `files_changed` is an intentional empty array (no-code-change verdict), no fallback is triggered and mechanical checks are correctly skipped.

The awk tracks streaks of added comment lines and resets the counter when a non-comment added line appears. Exits 0 if any streak reaches 3+. If it exits 0, flag a finding for large commented-out code blocks.

These pipelines return non-zero when no matches are found -- that is expected, not an error. Record any matches as findings.

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

Be honest. If the fix looks good, write an empty array. Do not invent problems.

## Gotchas

- If `files_changed` is empty and the verdict is a no-code-change type (`already_fixed`, `not_a_bug`, etc.), mechanical checks are correctly skipped. Do not flag this as an error.
- Debug print detection (`console.log`, `print(`, etc.) may match legitimate logging. Check the surrounding context before flagging -- only flag prints that look like debugging artifacts.
- The diff range `HEAD~1..HEAD` assumes the implement skill committed exactly once. In multi-iteration resolve runs where implement commits more than once, only the latest commit is diffed. The verdict's `files_changed` (the primary source) covers all changes regardless of commit count, so this only matters when falling back to git.
- Do not flag scope creep for changes to shared helpers, types, or test utilities when those files are legitimately needed by the fix.
