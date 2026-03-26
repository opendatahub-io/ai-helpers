---
name: coderabbit-review
description: Evaluate CodeRabbit PR comments and fix or reply
argument-hint: [pr-number]
compatibility: Requires gh CLI and GitHub MCP tools.
allowed-tools: Bash(gh pr view:*) Bash(gh repo view:*) Bash(git remote:*) Bash(git branch:*) Bash(gh pr list:*) Bash(curl:*) Bash(sha256sum:*) Read Glob Grep Edit AskUserQuestion mcp__github__pull_request_read mcp__github__add_reply_to_pull_request_comment mcp__github__add_issue_comment
---

# CodeRabbit PR Review Handler

Fetch CodeRabbit comments from a GitHub PR, evaluate each one, and take action: apply a code fix or post a reply.

The following GitHub MCP tools are available and ready to use directly — no ToolSearch required:
- `mcp__github__pull_request_read` — fetch PR comments and review threads
- `mcp__github__add_reply_to_pull_request_comment` — reply to inline review comments
- `mcp__github__add_issue_comment` — post PR-level comments

**PR:** $ARGUMENTS

## Step 1: Resolve the PR and Repository

If `$ARGUMENTS` is provided, use it as the PR number. Get the upstream repo:
```
gh repo view --json owner,name
```
Store: `owner`, `repo`, `pullNumber`.

If `$ARGUMENTS` is empty, detect the PR from the current branch. PRs are often opened from a fork, so `gh pr view` against the upstream may fail. Use this sequence:

1. Get the upstream owner/repo:
   ```
   gh repo view --json owner,name
   ```

2. Try to find the PR on the upstream first:
   ```
   gh pr view --repo <owner>/<repo> --json number,url,headRefName,baseRefName,title
   ```

3. If that fails (exit code non-zero or "no pull requests found"), get the current branch name and list all open PRs, matching by `headRefName`. The `--head fork-user:branch` filter is unreliable with `gh pr list` (returns empty even when the PR exists):
   ```
   branch=$(git branch --show-current)
   gh pr list --repo <owner>/<repo> --state open --json number,title,headRefName --limit 50
   ```
   Then match the entry where `headRefName == <branch>`.

4. If still not found (no matching headRefName), ask the user to identify the PR number:
   ```
   gh pr list --repo <owner>/<repo> --state open --json number,title,headRefName --limit 20
   ```

Store: `owner`, `repo`, `pullNumber`.

## Step 2: Fetch CodeRabbit Comments

Use the GitHub MCP tools to fetch comments.

**Inline review comments** (CodeRabbit's line-level suggestions):
Use `mcp__github__pull_request_read` with:
- `method: "get_review_comments"`
- `owner`, `repo`, `pullNumber`

**PR-level comments** (CodeRabbit's summary/walkthrough):
Use `mcp__github__pull_request_read` with:
- `method: "get_comments"`
- `owner`, `repo`, `pullNumber`

Filter both lists to only comments where `user.login` equals `coderabbitai[bot]`.

If no CodeRabbit comments are found, report that and exit.

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

```
# CodeRabbit Comments on PR #<N>

| # | File | Line | Category | Validity | Recommended Action | Summary |
|---|------|------|----------|----------|--------------------|--------|
| 1 | src/foo.ts | 42 | bug | valid | fix | "Variable x may be undefined" |
| 2 | src/bar.ts | 10 | style | nitpick | reply | "Consider using const here" |
```

Then show the full evaluation for each comment (bugs and security first, then performance, then others):

---

### Comment #N — [Category] — [File:Line or PR-level]

**CodeRabbit says:**
> [exact quote]

**Context** (relevant code snippet):
```
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
  - Skip (Do nothing with this comment)

**If `AskUserQuestion` returns an empty answer:** proceed with the recommended action for that comment and note what was done. Do not retry the same question.

## Step 5: Execute Actions

**For "Apply fix":**
1. If the fix involves externally-sourced values (SHA256 hashes, version strings, URLs suggested by CodeRabbit), **verify them independently** before applying:
   - For checksums: download the artifact and run `sha256sum` to confirm
   - For version/URL claims: fetch the upstream release page to confirm
   - CodeRabbit uses web search internally and can return incorrect values
2. Apply the change using the Edit tool
3. Show a confirmation of what changed

**For "Post reply" (inline review comment):**
Use `mcp__github__add_reply_to_pull_request_comment` with:
- `owner`, `repo`, `pullNumber`
- `commentId`: the `id` field of the CodeRabbit comment
- `body`: the draft reply text

**For "Post reply" (PR-level comment):**
Use `mcp__github__add_issue_comment` with:
- `owner`, `repo`
- `issue_number`: the PR number
- `body`: the draft reply text

**For "Edit & post":**
Use `AskUserQuestion` to ask the user to provide their edited reply text, then post it using the same MCP tool as above.

**For "Skip":**
Move on.

## Step 6: Summary

After all comments are processed:

```
# CodeRabbit Review — Done

## Actions taken:
- Fixed: N comment(s) — code changes applied
- Replied: N comment(s) — replies posted to PR
- Skipped: N comment(s)

## Next steps:
- If code was changed: commit and push to the **fork branch** that feeds the PR (not the upstream repo). Use `git remote -v` and `git branch -a` to confirm the correct remote and branch before pushing.
- If only replies were posted: CodeRabbit may re-evaluate on re-review trigger
```

## Notes

- CodeRabbit bot login is exactly `coderabbitai[bot]` — filter by this
- For inline review comments: key fields are `id`, `path`, `line`, `original_line`, `diff_hunk`, `body`
- For PR-level comments: key fields are `id`, `body`, `user.login`
- Be professional and concise in replies — acknowledge valid points, politely explain disagreements
- For nitpicks: "Thanks, noted — will address in a cleanup pass" is often the right reply
- NEVER post a reply or edit a file without explicit user approval
