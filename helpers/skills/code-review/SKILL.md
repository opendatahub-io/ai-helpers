---
name: code-review
description: >
  Perform AI code review on a GitLab MR or local branch. Reviews all commits
  since the base branch, produces structured JSON feedback with inline comments,
  and posts results to GitLab (CI) or displays them locally.
  Use when asked to review code changes, do a code review, or run ai-review.
allowed-tools: Bash Read Grep Glob
user-invocable: true
argument-hint: "[additional review instructions]"
compatibility: Requires python3, uv, and git. For CI posting requires GITLAB_API_TOKEN.
metadata:
  author: ODH
  version: "1.0"
  tags: code-review, gitlab, ci
---

# AI Code Review

Perform a structured code review of the current branch's changes and post
results to GitLab (in CI) or display them locally.

## Step 1: Review Code Changes

Review ALL commits in the branch since the base branch. The git workspace is
already checked out with the branch to review. Use git commands to inspect the
changes — do NOT access remote APIs (e.g., `glab` commands).

```bash
git log --oneline origin/main..HEAD
git diff origin/main..HEAD
```

Adjust the base branch name if different from `main` (e.g., `master`, `develop`).
In CI, `$CI_MERGE_REQUEST_DIFF_BASE_SHA` identifies the exact base commit.

**Only review the committed diff between branches.** Do NOT run `git status`,
do NOT report on untracked files, and do NOT include uncommitted working-tree
changes in your review.

### Review Guidelines

$ARGUMENTS

If no additional instructions were provided above, follow these defaults:

Provide constructive feedback that helps maintain code quality and follows
project best practices. Be selective and focused: only comment on issues that
genuinely matter. Do not comment for the sake of commenting. If the code is
well-written and follows best practices, it is perfectly acceptable to return
zero inline comments. Prioritize critical and major issues over minor stylistic
preferences. Avoid repeating the same type of feedback across multiple
locations — one representative comment is sufficient.

When referencing coding standards, security norms, best practices, or
component-specific behavior, search for and cite the authoritative source
(official documentation, RFCs, upstream references) to back up the claim.

## Step 2: Produce Review JSON

Write your review output as a JSON file at `/tmp/ai-review-output.json`.

The JSON **must** be a valid object matching this schema exactly:

```json
{
  "summary": "Brief overall assessment of the changes (2-4 sentences, markdown allowed inside this string)",
  "positive_aspects": ["List of good practices and well-implemented features"],
  "inline_comments": [
    {
      "file": "path/to/file (relative to repo root)",
      "line": 42,
      "severity": "critical|major|minor|suggestion",
      "comment": "Description of the issue and suggested fix (markdown allowed inside this string)"
    }
  ],
  "fix_prompt": "Optional: a copy-paste prompt to fix all issues found. Omit this field if there are no actionable fixes."
}
```

### Inline comments rules

- ONLY comment on lines that appear in the diff (changed or added lines).
  Do NOT comment on unchanged lines.
- Use the line number as it appears in the NEW version of the file.
- `file` must be the path relative to the repository root
  (e.g., `src/main.py`, not `/workspace/src/main.py`).
- Severity levels:
  - **critical**: Security vulnerabilities, build-breaking changes
  - **major**: Significant logic errors, pattern violations
  - **minor**: Style issues, minor improvements
  - **suggestion**: Optional improvements for code quality
- Each comment should be self-contained and actionable.
- If there are no inline issues to report, use an empty array `[]`.

### Summary rules

- Keep it short (2-4 sentences). The inline comments carry the detail.
- Mention the overall quality and any critical concerns.

### Positive aspects rules

- List 1-3 things done well. If nothing stands out, use an empty array `[]`.

### Fix prompt rules

- Omit this field entirely if there are no actionable fixes.

## Step 3: Post Results

Run the `review.py` script from this skill's `scripts/` directory.
Execute it directly (not via `python`) to invoke uv via the shebang:

```bash
./scripts/review.py post /tmp/ai-review-output.json
```

The script auto-detects the platform (GitLab CI, GitHub, or local) and handles:

- JSON validation and chill-mode filtering (controlled by `$CHILL_MODE` env var)
- Deduplication against previous reviews (skips comments on unchanged code)
- Deleting previous AI review discussions on the MR (GitLab)
- Posting inline comments and a summary note to the MR (GitLab)
- Falling back to formatted terminal display when no CI platform is detected

If the script reports a JSON parse error, fix the JSON in
`/tmp/ai-review-output.json` and re-run the command.

## Step 4: Report Results

After the script completes successfully:

- **CI**: Confirm the review was posted to the merge request
- **Local**: The script displays results directly in the terminal
- **Errors**: Report any failures from the script output

## Gotchas

- Line numbers in `inline_comments` must reference the NEW file version, not the old one; using old-side line numbers causes comments to land on the wrong line in GitLab.
- The JSON output must be strict JSON (no trailing commas, no comments). Invalid JSON will cause the posting script to fail.
- Running `git status` or reviewing uncommitted changes will produce false findings that are not part of the MR diff.

## Environment Variables

The Python script reads these from the environment. In GitLab CI, most are
set automatically — no manual configuration needed.

### GitLab

| Variable | Required for | Default | Description |
|----------|-------------|---------|-------------|
| `GITLAB_API_TOKEN` | CI/MR | — | GitLab Personal Access Token |
| `CI_SERVER_URL` | — | `https://gitlab.com` | GitLab server URL |
| `CI_PROJECT_ID` | CI/MR | — | GitLab project ID |
| `CI_MERGE_REQUEST_IID` | CI/MR | — | Merge request IID |
| `CI_MERGE_REQUEST_DIFF_BASE_SHA` | CI/MR | — | Base SHA for diff positioning |
| `CI_COMMIT_SHA` | CI/MR | — | Head commit SHA |
| `CI_JOB_NAME` | — | `ai-review` | Job name for summary footer |
| `CI_JOB_URL` | — | `#` | Job URL for summary footer |

### Common

| Variable | Required for | Default | Description |
|----------|-------------|---------|-------------|
| `CHILL_MODE` | — | `true` | Filter out suggestion-level comments |
| `VERBOSE` | — | `false` | Show detailed API error responses |
