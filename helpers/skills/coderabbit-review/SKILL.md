---
name: coderabbit-review
description: Use when you need to evaluate CodeRabbit PR comments and fix or reply
argument-hint: [pr-number]
compatibility: Requires gh CLI.
allowed-tools: Bash(gh pr view:*) Bash(gh repo view:*) Bash(git remote:*) Bash(git branch:*) Bash(gh pr list:*) Bash(gh api:*) Bash(curl:*) Bash(sha256sum:*) Read Glob Grep Edit AskUserQuestion
---

# CodeRabbit PR Review Handler

Fetch CodeRabbit comments from a GitHub PR, evaluate each one, and take action: apply a code fix or post a reply.

**PR:** $ARGUMENTS

## Step 1: Resolve the PR and Repository

Determine the `owner`, `repo`, and `pullNumber`:

- If `$ARGUMENTS` is a PR number, use it directly.
- Otherwise, detect the PR from the current branch using `gh pr view` or `gh pr list`.
- Use `gh repo view --json owner,name` to get the upstream coordinates. If that fails (e.g., no default remote set), fall back to parsing `git remote -v` to identify the upstream GitHub repository.
- The repo may be a fork with multiple remotes. Do not assume names like `upstream`/`origin`. Prefer repo coordinates from PR metadata (`gh pr view --json`), then `gh repo view`, then `git remote -v`. If multiple candidates remain, ask the user.
- If you cannot determine the PR automatically, ask the user.

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

After presenting ALL comments, **wait for the user to respond**. The user may want to:

- **Discuss** — ask questions, understand a comment better, debate whether it's valid. Act as a knowledgeable colleague: explain the trade-offs, share context, help them form their own opinion. Stay in this discussion mode as long as the user is engaging. Do NOT push toward action or present menus while the user is still exploring.
- **Act** — when the user indicates they're ready (e.g., "let's fix these", "go ahead", "apply #1 and #3"), proceed with the requested actions.
- **Decide per-comment** — if the user wants to go through comments one by one, walk through each and ask what to do.

When the user is ready to act, the available actions per comment are:
- **Apply fix** — apply the code change (only when a fix is proposed)
- **Post reply** — post the draft reply to the PR
- **Edit & post** — let the user adjust the reply text first, then post
- **Skip** — do nothing with this comment

**Critical rule:** Never apply fixes or post replies without explicit user approval. If unsure whether the user wants to act or keep discussing, keep discussing.

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
- If code was changed: do NOT lump all changes into a single generic commit. Group related changes into **separate logical commits**, each with a message that explains *why* the change was made (not just "address CodeRabbit feedback"). Unrelated fixes from different CodeRabbit comments should be separate commits. Push to the **PR head branch** (fork or same-repo, whichever feeds the PR). Use `gh pr view --json headRefName,headRepositoryOwner` plus `git remote -v` and `git branch -a` to confirm destination before pushing.
- If only replies were posted: CodeRabbit may re-evaluate on re-review trigger

## Notes

- CodeRabbit bot login is exactly `coderabbitai[bot]` — filter by this
- For inline review comments: key fields are `id`, `path`, `line`, `original_line`, `diff_hunk`, `body`
- For PR-level comments: key fields are `id`, `body`, `user.login`
- Be professional and concise in replies — acknowledge valid points, politely explain disagreements
- For nitpicks: "Thanks, noted — will address in a cleanup pass" is often the right reply
- NEVER post a reply or edit a file without explicit user approval

## Gotchas

- CodeRabbit's bot login is exactly `coderabbitai[bot]` — using any other string (e.g., `coderabbit`) will silently miss all comments.
- Walkthrough and summary posts look like actionable comments but must be filtered out by checking for `<!-- walkthrough_start -->` markers.
- Externally-sourced values in CodeRabbit suggestions (SHA256 hashes, version strings) can be wrong — always verify independently before applying.
