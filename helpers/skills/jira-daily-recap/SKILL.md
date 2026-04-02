---
name: jira-daily-recap
description: >-
  Post a daily work summary as a Jira comment by collecting GitHub commits/PRs
  and Cursor chat history for the day. Use when the user asks to update a Jira
  ticket with today's work, log daily progress on a ticket, post a Jira comment
  with what was done, or runs /jira-daily-recap.
user-invocable: true
argument-hint: "<JIRA-KEY> <owner/repo> [branch] [date]"
allowed-tools: "Bash, GitHub MCP, Atlassian MCP"
---

# Jira Daily Recap

Collect a single day's GitHub activity and Cursor chat history **scoped to the
specified repository/project**, then post a concise comment on a Jira ticket
summarizing what was accomplished on that project only.

## Usage

```text
/jira-daily-recap <JIRA-KEY> <owner/repo> [branch] [date]
```

- `JIRA-KEY` — required (e.g. `RHOAIENG-12345`)
- `owner/repo` — required GitHub repository (e.g. `openshift/kubeflow`)
- `branch` — optional; defaults to the repo's default branch
- `date` — optional `YYYY-MM-DD`; defaults to **today**. When provided, collect
  activity only for that specific date (not a range from that date to today).

If the user omits required arguments, ask for them before proceeding.
The date can also be given in natural language (e.g. "for March 3rd") — resolve
it to `YYYY-MM-DD` before proceeding.

## Step-by-Step

### 1. Resolve identities

- **GitHub username** — try these in order until one succeeds:
  1. Call GitHub MCP `get_me`.
  2. Run `gh api /user --jq .login` (GitHub CLI).
  3. Run `git config user.name` as a last resort (may differ from GitHub handle).
- **Jira cloud ID** — call Jira MCP `getAccessibleAtlassianResources` to get the
  `cloudId`.
- **Validate ticket** — call Jira MCP `getJiraIssue` with `cloudId` and
  `issueIdOrKey` (the JIRA-KEY) to confirm the ticket exists. Use
  `responseContentFormat: "markdown"`. Extract the issue summary for context.

### 2. Collect GitHub activity (target date only)

Let `TARGET_DATE` = the user-supplied date or today's date as `YYYY-MM-DD`.

**Commits:**
- Call GitHub MCP `list_commits` with `owner`, `repo`, `sha` (branch if given),
  and `author` set to the GitHub username from step 1.
- Filter to commits where `commit.author.date` starts with `TARGET_DATE`.
- Keep: commit message (first line) and SHA (short, first 7 chars).
- If no commits match `TARGET_DATE` exactly, record zero commits — do NOT
  include commits from other days.

**Pull Requests:**
- Call GitHub MCP `search_pull_requests` with query:
  `repo:<owner>/<repo> author:<username> updated:<TARGET_DATE>..<TARGET_DATE>`
  (GitHub's `..` range is inclusive on both bounds, so using the same date on
  both sides restricts results to exactly `TARGET_DATE`)
- Keep: PR title, number, state (open/closed/merged), URL.

### 3. Collect Cursor chat history (target date only, scoped to repo)

- **Input validation:** Verify that `owner` and `repo` each match the pattern
  `^[A-Za-z0-9._-]+$`. If either contains path separators (`/`, `\`) or other
  special characters beyond this set, reject the input and inform the user.
- Identify the Cursor project folder that corresponds to the specified
  `owner/repo`. Transcript directories live under `~/.cursor/projects/` with
  platform-specific slugs (e.g. `Users-<user>-CODING-<repo>` on macOS,
  `home-<user>-<repo>` on Linux). Match on the **repo name portion** of the
  workspace slug.
- After resolving the path, verify it is still under `~/.cursor/projects/` to
  prevent directory traversal.
- List `.jsonl` files **only under that project's** `agent-transcripts/` folder.
  Use file mtime as a quick pre-filter: skip files last modified before
  `TARGET_DATE` (they cannot contain messages from that day).
- **Do NOT** collect transcripts from other project folders — only the project
  matching the specified repo is in scope.
- For each candidate `.jsonl` file, read its lines and extract user messages:
  - If a JSON line contains a timestamp field (e.g. `createdAt`, `timestamp`),
    use it to determine the message date. **Only include messages whose
    timestamp falls on `TARGET_DATE`.**
  - If no per-line timestamp is available, fall back to the file's mtime —
    include messages only when the file was last modified on `TARGET_DATE`.
  - Prefer text inside `<user_query>...</user_query>` tags.
  - Fall back to the first 200 chars of user message text.
- Never include messages from other dates regardless of filtering method.
- Distill into a short list of what the user worked on / asked the agent to do
  **for this project/Jira ticket**.
- Deduplicate similar entries. Aim for 3-5 distinct activity bullets.
- Ignore meta/skill invocations (e.g. `/jira-daily-recap`, `/update-internship-tasks`,
  single-word messages, or messages that are only tool scaffolding).
- **Exclude any work unrelated to the specified repo or Jira ticket** — even if
  it appears in matching transcripts (e.g. side conversations about other projects).
- **Only extract concrete, actionable progress** — code changes, bug fixes, new
  features, config updates, PR/review work, or investigation with a clear outcome.
  Discard casual conversation, questions about how things work, troubleshooting
  that led nowhere, setup/environment chatter, and requests to run this skill.
  If a transcript message didn't result in a tangible deliverable, skip it.

### 4. Gate check — verify real activity exists for TARGET_DATE

Before composing any comment, confirm that **at least one** of the following is true:
- There is at least one GitHub commit authored on **`TARGET_DATE`**.
- There is at least one PR updated on **`TARGET_DATE`**.
- There is at least one transcript file modified on **`TARGET_DATE`** containing
  substantive user messages (coding questions, feature work, debugging, design
  decisions).

**If none of these are true → STOP. Do NOT post a Jira comment. Tell the user:**
> "No activity found for <TARGET_DATE>. No Jira comment was posted."

**CRITICAL:** Never recycle or restate work from other days. If the only evidence
is commits or transcripts from different dates, that is zero activity for
`TARGET_DATE` — stop and report it.

### 5. Compose the Jira comment

Merge all sources into a concise progress update. Use this template:

```text
**Progress update — <TARGET_DATE> (AI generated)**

- <bullet 1: what was done, with PR/commit link if applicable>
- <bullet 2>
- <bullet 3>
- ...
```

Rules:
- 3-5 bullets max. Each bullet is one sentence.
- Lead with the most impactful work.
- Inline GitHub links where relevant: `[PR #123](https://github.com/owner/repo/pull/123)`.
- Combine related commits + chat activity into a single bullet when they describe the same work.
- Do NOT list raw commit SHAs unless there's no PR to link.
- Do NOT include filler like "continued working on…" — be specific.
- Only include work from **`TARGET_DATE`**. Never include work from other days.
- **Only include work related to the specified repo and Jira ticket.** Do NOT
  mix in activity from other projects, repos, or unrelated Jira tickets.
- If no activity found for a source, omit it silently.

### 6. Post to Jira

- Call Jira MCP `addCommentToJiraIssue` with:
  - `cloudId` from step 1
  - `issueIdOrKey` — the JIRA-KEY
  - `commentBody` — the composed comment
  - `contentFormat: "markdown"`
- Confirm success and show the user the posted comment text.

### 7. Show output in chat

Always display the final comment in chat so the user can review what was posted.
Format it clearly with a heading like:

```text
✅ Comment posted to <JIRA-KEY>:
<the comment body>
```

## Failure Handling

- If Jira MCP is unavailable or auth fails → output the comment in chat and
  instruct the user to paste it manually.
- If GitHub MCP is unavailable → try fetching GitHub data via the GitHub CLI
  (`gh api`) or `curl` against `https://api.github.com` as a fallback. If that
  also fails, skip GitHub data and build the comment from chat history only.
- If no transcripts found for `TARGET_DATE` → skip chat data, build comment
  from GitHub only.
- If both sources are empty for `TARGET_DATE` → inform the user:
  "No activity found for <TARGET_DATE>."
- If the Jira ticket key is invalid → report the error and stop.

## Example

User runs: `/jira-daily-recap RHOAIENG-53408 openshift/kubeflow release-1.9`

Posted comment:

```text
**Progress update — 2026-04-01 (AI generated)**

- Rebased SDK PR #368 on latest upstream and resolved merge conflicts
- Added unit tests for the new TrainingClient checkpoint API
- Investigated nvcc build failure blocking RHOAIENG-56094 ([PR #705](https://github.com/openshift/kubeflow/pull/705))
```
