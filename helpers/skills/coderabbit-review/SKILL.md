---
name: coderabbit-review
description: Evaluate CodeRabbit PR comments and fix or reply
argument-hint: [pr-number]
compatibility: Requires gh CLI.
allowed-tools: Bash(gh pr view:*) Bash(gh repo view:*) Bash(git remote:*) Bash(git branch:*) Bash(gh pr list:*) Bash(gh api:*) Bash(curl:*) Bash(sha256sum:*) Read Glob Grep Edit AskUserQuestion
---

# CodeRabbit PR Review Handler

Fetch CodeRabbit comments from a GitHub PR, evaluate each one, and take action: apply a code fix or post a reply.

**PR:** $ARGUMENTS

## Step 1: Resolve the PR and Repository

If `$ARGUMENTS` is provided, use it as the PR number. Get the upstream repo:
```bash
gh repo view --json owner,name
```
Store: `owner`, `repo`, `pullNumber`.

If `$ARGUMENTS` is empty, detect the PR from the current branch. PRs are often opened from a fork, so `gh pr view` against the upstream may fail. Use this sequence:

1. Get the upstream owner/repo:
   ```bash
   gh repo view --json owner,name
   ```

2. Try to find the PR on the upstream first:
   ```bash
   gh pr view --repo <owner>/<repo> --json number,url,headRefName,baseRefName,title
   ```

3. If that fails (exit code non-zero or "no pull requests found"), get the current branch name and list all open PRs, matching by `headRefName` and `headRepositoryOwner`. The `--head fork-user:branch` filter is unreliable with `gh pr list` (returns empty even when the PR exists):
   ```bash
   branch=$(git branch --show-current)
   gh pr list --repo <owner>/<repo> --state open --json number,title,headRefName,headRepositoryOwner --limit 50
   ```
   Then match the entry where `headRefName == <branch>` AND `headRepositoryOwner.login` matches the expected fork owner. If multiple matches remain, stop and ask the user to pick the PR number explicitly.

4. If still not found (no matching headRefName), ask the user to identify the PR number:
   ```bash
   gh pr list --repo <owner>/<repo> --state open --json number,title,headRefName,headRepositoryOwner --limit 20
   ```

Store: `owner`, `repo`, `pullNumber`.

## Step 2: Fetch CodeRabbit Comments

**Inline review comments** (CodeRabbit's line-level suggestions):
```bash
gh api --paginate repos/<owner>/<repo>/pulls/<pullNumber>/comments
```

**PR-level comments** (CodeRabbit's summary/walkthrough):
```bash
gh api --paginate repos/<owner>/<repo>/issues/<pullNumber>/comments
```

Filter both lists to only comments where `user.login` equals `coderabbitai[bot]`.

For PR-level comments, skip any comment whose body contains `<!-- walkthrough_start -->` or `<!-- This is an auto-generated comment: review in progress` — these are CodeRabbit's walkthrough/summary posts, not actionable review feedback.

For inline comments, skip any comment that belongs to a resolved review thread (check the `pull_request_review_id` against resolved threads, or look for the `"resolved": true` marker if available).

If no actionable CodeRabbit comments are found, report that and exit.

## Step 3: Evaluate Each Comment

For each CodeRabbit comment, analyze it carefully by reading the relevant source file(s).

For inline comments: use the `path` field to read the file with the Read tool. Use `line` or `original_line` to find the exact code location. The `diff_hunk` field shows the surrounding context.

Evaluate:

1. **Category**: classify as one of:
   - `bug` — actual code defect or logic error
   - `security` — security vulnerability
   - `performance` — inefficiency or resource issue
   - `style` — formatting, naming, readability
   - `docs` — missing or incorrect documentation/comments
   - `nitpick` — minor preference, not a real issue
   - `question` — CodeRabbit is asking for clarification

2. **Validity**: does the comment point to a real issue?
   - `valid` — yes, should be addressed
   - `debatable` — reasonable disagreement exists
   - `invalid` — the code is correct and CodeRabbit is wrong

3. **Recommended action**:
   - `fix` — the code should be changed; generate the fix
   - `reply` — explain why the code is correct, or acknowledge and defer
   - `dismiss` — noise; briefly acknowledge and move on

## Step 4: Present Summary and Batch Decision

Show a summary table first:

# CodeRabbit Comments on PR #<N>

| # | File | Line | Category | Validity | Recommended Action | Summary |
|---|------|------|----------|----------|--------------------|---------|
| 1 | src/foo.ts | 42 | bug | valid | fix | "Variable x may be undefined" |
| 2 | src/bar.ts | 10 | nitpick | debatable | reply | "Consider using const here" |

Then show the full evaluation for each comment (bugs and security first, then performance, then others):

---

## Comment #N — [Category] — [File:Line or PR-level]

**CodeRabbit says:**
> [exact quote]

**Context** (relevant code snippet):
```text
[code from the file at that location]
```

**Assessment:**
[Your evaluation: why valid/invalid, what the actual issue is]

**Proposed action:** `fix` | `reply` | `dismiss`

[If `fix`: show the exact code diff to apply]

[If `reply` or `dismiss`: show the draft reply text]

---

After presenting ALL comments, use `AskUserQuestion` to offer a **batch option first**:

Question: "How would you like to process these comments?"
Header: "Mode"
Options:
  - Auto (Apply recommended action for each: fix valid ones, reply to others)
  - Per-comment (Review and decide each comment individually)

**If "Auto":** proceed with all recommended actions without further prompting, then report what was done.

**If "Per-comment":** for each comment, ask:

Question: "What should we do with CodeRabbit comment #N ([category]: [short description])?"
Header: "Action"
Options:
  - Apply fix (Apply the code change as shown)      [only when action is `fix`]
  - Post reply (Post the draft reply to the PR)
  - Edit & post (Let me adjust the reply first)
  - Dismiss (Post a brief acknowledgement and move on)  [only when action is `dismiss`]
  - Skip (Do nothing with this comment)

**If `AskUserQuestion` returns an empty answer:** do not apply fixes or post replies. Mark the comment as `skipped (no explicit approval)` and continue.

## Step 5: Execute Actions

**For "Apply fix":**
1. If the fix involves externally-sourced values (SHA256 hashes, version strings, URLs suggested by CodeRabbit), **verify them independently** before applying:
   - For checksums: download the artifact and run `sha256sum` to confirm
   - For version/URL claims: fetch only from known allowlisted HTTPS domains (e.g., github.com, pypi.org); reject localhost, link-local, and private IP ranges. Use hardened curl flags: `--proto '=https' --tlsv1.2 --fail --location --max-time 15 --connect-timeout 5`
   - CodeRabbit uses web search internally and can return incorrect values
2. Apply the change using the Edit tool
3. Show a confirmation of what changed

**For "Post reply" (inline review comment):**
```bash
gh api -X POST repos/<owner>/<repo>/pulls/<pullNumber>/comments/<commentId>/replies -f body="<reply text>"
```

**For "Post reply" (PR-level comment):**
```bash
gh api -X POST repos/<owner>/<repo>/issues/<pullNumber>/comments -f body="<reply text>"
```

**For "Edit & post":**
Use `AskUserQuestion` to ask the user to provide their edited reply text, then post it using the appropriate `gh api` call above.

**For "Skip":**
Move on.

## Step 6: Summary

After all comments are processed, output:

# CodeRabbit Review — Done

## Actions taken:
- Fixed: N comment(s) — code changes applied
- Replied: N comment(s) — replies posted to PR
- Dismissed: N comment(s) — brief acknowledgements posted
- Skipped: N comment(s)

## Next steps:
- If code was changed: commit and push to the **fork branch** that feeds the PR (not the upstream repo). Use `git remote -v` and `git branch -a` to confirm the correct remote and branch before pushing.
- If only replies were posted: CodeRabbit may re-evaluate on re-review trigger

## Notes

- CodeRabbit bot login is exactly `coderabbitai[bot]` — filter by this
- For inline review comments: key fields are `id`, `path`, `line`, `original_line`, `diff_hunk`, `body`
- For PR-level comments: key fields are `id`, `body`, `user.login`
- Be professional and concise in replies — acknowledge valid points, politely explain disagreements
- For nitpicks: "Thanks, noted — will address in a cleanup pass" is often the right reply
- NEVER post a reply or edit a file without explicit user approval
