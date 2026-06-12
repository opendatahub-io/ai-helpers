# Jira daily recap — full workflow

Detailed steps for **`jira-daily-recap`**. The skill root describes usage; execute this document when running the recap.

---

## 0. Validate `owner` and `repo` (before any GitHub, shell, or filesystem use)

- Split the required `owner/repo` argument into `owner` and `repo`.
- Verify **each** segment matches `^[A-Za-z0-9._-]+$`. Reject `/`, `\`,
  whitespace, shell metacharacters, or oversized strings — **stop** with a
  clear error. Reuse this validated pair unchanged in Steps 2, 3, and all
  `gh api` / `curl` calls (no late re-parsing).

## Step-by-Step

### 1. Resolve identities

- **Validate `JIRA-KEY`** — must match `^[A-Za-z][A-Za-z0-9]+-\d+$`. If it does
  not, stop and ask for a valid key (prevents injection oddities in API calls).
- **GitHub username (must be login handle, not display name)** — resolve in order
  until one returns a plausible GitHub handle:
  1. `gh api /user --jq .login`.
  2. `git config github.user`.
  3. Optionally parse `git remote get-url origin` when it clearly encodes the
     contributor handle (e.g. `git@github.com:LOGIN/somerepo.git` → take `LOGIN`
     before the first slash only if `LOGIN` fits `^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?$`).
  If still unresolved after the chain above, either **ask the user for their
  GitHub login** or — if `git config user.email` returns a value — fetch commits
  without `--author` and **post-filter** where `commit.author.email` (or
  `committer.email`) equals that address (case-normalized), still applying
  **`TARGET_DATE` / `TARGET_TZ`** filtering. Do **not** use `git config user.name`
  as an author filter.
- **Jira cloud ID** — call Jira MCP `getAccessibleAtlassianResources` to get the
  `cloudId`.
- **Validate ticket** — call Jira MCP `getJiraIssue` with `cloudId` and
  `issueIdOrKey` (the JIRA-KEY) to confirm the ticket exists. Use
  `responseContentFormat: "markdown"`. Extract the issue summary for context.

### 2. Collect GitHub activity (target date only)

- Let `TARGET_TZ` = timezone for calendar boundaries: use an IANA name the user
  gives (or names alongside "today"); if none is given, use **UTC** and note
  that choice when summarizing dates.
- Derive **`TARGET_DATE`** as `YYYY-MM-DD` **in `TARGET_TZ`** — user-supplied
  date interpreted in `TARGET_TZ`, or local "today" in `TARGET_TZ` when none is
  given.

**Commits:**

- Use the **`gh` CLI** to fetch commits:

```bash
gh api "repos/<owner>/<repo>/commits?sha=<branch>&author=<username>&per_page=100" --jq '.[] | {sha: .sha[0:7], date: .commit.author.date, msg: (.commit.message | split("\n") | .[0])}'
```

  When using email-based post-filter (no login resolved), omit `&author=` and
  filter client-side as described in step 1.
- If `gh api` fails, fall back to an authenticated `curl` request against
  `https://api.github.com/repos/<owner>/<repo>/commits?...` (use the token from
  `gh auth token` or the environment).
- For each commit, read the author timestamp from `.commit.author.date`. Parse
  ISO 8601 strictly; if parsing fails, treat that commit as **non-matching** for
  the date filter (do not guess). Convert successful parses to **`TARGET_TZ`**
  and compare the calendar date to **`TARGET_DATE`**.
- Keep: commit message (first line) and SHA (short, first 7 chars).
- If no commits match after conversion, record zero commits — do NOT pull other
  days.

**Pull Requests:**

- Build the search query as `repo:<owner>/<repo> updated:<TARGET_DATE>..<TARGET_DATE>`
  (GitHub's `..` is inclusive; same date twice restricts to that calendar day).
  **Append** `author:<username>` only when step 1 yielded a definite GitHub login.

```bash
gh api "search/issues?q=repo:<owner>/<repo>+is:pr+author:<username>+updated:<TARGET_DATE>..<TARGET_DATE>" --jq '.items[] | {number, title, state, html_url, updated_at}'
```

  If `gh api` fails, fall back to `curl` with the same URL against
  `https://api.github.com/search/issues`.
- For each candidate PR, prefer `updated_at`; if merging/closing dominates the
  story, also inspect `merged_at` / `closed_at` when present — normalize each
  timestamp into **`TARGET_TZ`** and keep the PR **only when at least one of
  these dates has calendar day `TARGET_DATE`**.
- Keep: PR title, number, state (open/closed/merged), URL.

### 3. Collect Cursor chat history (target date only, scoped to repo)

- Reapply the **`owner` / `repo` checks from Step 0** if inputs could have changed;
  inputs must remain the validated segments only.
- Identify the Cursor project folder that corresponds to the specified
  `owner/repo`. Transcript directories live under `~/.cursor/projects/` with
  platform-specific slugs (e.g. `Users-<user>-CODING-<repo>` on macOS,
  `home-<user>-<repo>` on Linux). Match on the **repo name portion** of the
  workspace slug.
- After resolving the project folder, **canonicalize** both the Cursor projects
  base (`~/.cursor/projects` expanded) and the candidate directory with `realpath`
  / `Path.resolve` (or equivalent). Ensure the project's resolved path **is that
  base directory or a strict subdirectory**: compare path segments so the base
  is a proper ancestor (not a brittle string prefix against paths like `.../projects_evil`).
  Reject `..`, escapes via symlinks, or anything outside the base.
- List `.jsonl` files **only under that project's** `agent-transcripts/` folder.
  Use file mtime as a quick pre-filter: skip files last modified before
  `TARGET_DATE` (they cannot contain messages from that day).
- **Do NOT** collect transcripts from other project folders — only the project
  matching the specified repo is in scope.
- For each candidate `.jsonl` file, read its lines and extract user messages:
  - If a JSON line contains a timestamp field (e.g. `createdAt`, `timestamp`),
    parse it to instant, convert into **`TARGET_TZ`**, and **only include
    messages whose local calendar date equals `TARGET_DATE`.**
  - If no per-line timestamp is available, fall back to the file's mtime —
    convert mtime instant to **`TARGET_TZ`** — include messages only when that
    local calendar date is **`TARGET_DATE`**.
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

- There is at least one GitHub commit whose author date lands on **`TARGET_DATE`**
  in **`TARGET_TZ`** (per step 2).
- There is at least one PR that step 2 kept for **`TARGET_DATE`** (normalized
  timestamps in **`TARGET_TZ`**).
- Step 3 yields **at least one substantive user message** that would appear in the
  recap using the same **`TARGET_DATE` / `TARGET_TZ`** rules (per-line timestamp
  preferred; otherwise mtime fallback); empty or irrelevant chatter alone does
  not pass.

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

- 3-5 bullets max. Each bullet is exactly **one sentence** after cleanup.
- Lead with the most impactful work.
- **Sanitize for Jira (all outward text):** apply the same rules to **commit
  first lines, PR titles, and transcript-derived prose** — paraphrase or strip
  control/markdown-surprise characters and raw HTML-ish `<...>` (except deliberate
  link targets you author); collapse `\n`/`\\t` to spaces; cap snippet length before
  composing bullets.
- If a candidate bullet still has multiple sentences after paraphrasing, keep
  only the **first** (split on sentence boundaries after `.`, `?`, or `!` once
  whitespace is collapsed); trim trailing commas; end with exactly one terminating `.`,
  `?`, or `!`.
- Inline GitHub links where relevant: `[PR #123](https://github.com/owner/repo/pull/123)`.
- Combine related commits + chat activity into a single bullet when they describe the same work.
- Do NOT list raw commit SHAs unless there's no PR to link.
- Do NOT include filler like "continued working on…" — be specific.
- Only include work from **`TARGET_DATE`** (honoring **`TARGET_TZ`**). Never pull other calendar days.
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

---

## Failure handling

- On any API error → show a **short, user-safe message** (no tokens, raw
  headers, or stack traces).
- If Jira MCP is unavailable or auth fails → output the comment in chat and
  instruct the user to paste it manually.
- If `gh api` fails → fall back to an authenticated `curl` request against
  `https://api.github.com/...` (use the token from `gh auth token` or the
  environment). If that also fails, skip GitHub data and compose from chat
  transcripts only (still enforce the Step 4 gate).
- If no transcripts found for `TARGET_DATE` → skip chat data, build comment
  from GitHub only.
- If both sources are empty for `TARGET_DATE` → inform the user:
  "No activity found for <TARGET_DATE>. No Jira comment was posted."
- If the Jira ticket key is invalid → report the error and stop.

---

## Example

User runs: `/jira-daily-recap RHOAIENG-53408 openshift/kubeflow release-1.9`

Posted comment:

```text
**Progress update — 2026-04-01 (AI generated)**

- Rebased SDK PR #368 on latest upstream and resolved merge conflicts.
- Added unit tests for the new TrainingClient checkpoint API.
- Investigated nvcc build failure blocking RHOAIENG-56094 ([PR #705](https://github.com/openshift/kubeflow/pull/705)).
```
