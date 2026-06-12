---
name: jira-daily-recap
description: >-
  Post a daily work summary as a Jira comment by collecting GitHub commits/PRs
  and Cursor chat history for the day. Use when the user asks to update a Jira
  ticket with today's work, log daily progress on a ticket, post a Jira comment
  with what was done, or runs /jira-daily-recap.
user-invocable: true
argument-hint: "<JIRA-KEY> <owner/repo> [branch] [date]"
allowed-tools: "Bash, Atlassian MCP"
---

# Jira Daily Recap

Collect a single day's GitHub activity and Cursor chat history **scoped to the
specified repository/project**, then post a concise comment on a Jira ticket
summarizing what was accomplished on that project only.

## Prerequisites

- **`gh`** CLI authenticated (`gh auth status` succeeds).
- Jira access via Atlassian MCP.
- Optional: local Cursor **`~/.cursor/projects/.../agent-transcripts/`** for chat history.

## Usage

```text
/jira-daily-recap <JIRA-KEY> <owner/repo> [branch] [date]
```

- `JIRA-KEY` — required (e.g. `RHOAIENG-12345`)
- `owner/repo` — required GitHub repository (e.g. `openshift/kubeflow`)
- `branch` — optional; defaults to the repo's default branch
- `date` — optional `YYYY-MM-DD`; defaults to **today**. When provided, collect
  activity only for that specific date (not a range from that date to today).
  Give an **IANA timezone** alongside natural-language dates so `TARGET_TZ` is
  unambiguous.

If the user omits required arguments, ask for them before proceeding.
Natural-language dates must resolve to **`YYYY-MM-DD`**, validate
`^\d{4}-\d{2}-\d{2}$`, and be a real calendar date; reject ambiguous inputs.

## Procedure

Execute the full numbered flow (validation → identities → GitHub → transcripts
→ gate → compose → post → echo), including failure handling and the example,
in **`references/workflow.md`**.

## Gotchas / caveats

- **Never** use `git config user.name` as the GitHub `author=` parameter — use a
  real login or email-based post-filter as described in the workflow reference.
- **Validate `owner` and `repo` before any API, shell, or filesystem use** —
  malformed values can confuse paths or injected CLI arguments.
- **Default timezone** when the user omits one: **`TARGET_TZ` = UTC** — "today"
  and commit timestamps may differ from the user's local midnight.
- **Wrong Cursor project folder** (slug mismatch, symlink escape): always
  canonicalize paths and ensure the transcript directory is a **strict
  subdirectory** of `~/.cursor/projects` before reading `.jsonl` files.
- **`gh` CLI fails**: if `gh api` errors out, fall back to authenticated `curl`
  (token via `gh auth token`); if all GitHub sources fail, compose from
  transcripts only but **Step 4** still blocks a post when nothing qualifies for
  **`TARGET_DATE`**.
- **Jira markdown**: sanitize commit titles, PR titles, and transcript text before
  `commentBody` — do not paste unescaped control markup or arbitrary HTML-like
  payloads.
