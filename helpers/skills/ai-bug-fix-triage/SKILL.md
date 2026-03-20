---
name: ai-bug-fix-triage
description: Triage JIRA bugs against repository code to classify AI fixability. Use when reviewing a backlog of bugs to determine which ones an AI agent can fix.
allowed-tools: Bash Read Grep Glob
---

# Bug Triage

Triage JIRA bugs from a project backlog against a loaded repository to determine which bugs an AI agent can fix. Produces a focused fixability report.

## Scope

This skill answers one question: **can an AI agent fix this bug in this repo?** It classifies issues as AI-Fixable, Needs Human, or Needs Info based on a fixability rubric.

"Bug" is used broadly here — analyze **Bugs and Stories** for fixability. Skip **Epics, Initiatives, and Features** as they are too high-level for a single code fix (note them as skipped in the report).

**Out of scope:**

- **Deduplicate bugs** — does not detect or merge duplicate tickets
- **Prioritize or re-rank severity** — respects the existing JIRA priority as-is
- **Estimate effort** — no story points, t-shirt sizes, or time estimates

## Prerequisites

- **Atlassian MCP** configured and authenticated (provides `getAccessibleAtlassianResources`, `searchJiraIssuesUsingJql`, `getJiraIssue`, `editJiraIssue`, `addCommentToJiraIssue`)
- **Target repository** loaded in the workspace — the user will have it open or will specify it
- **AGENTS.md or CLAUDE.md** present in the repo (used to understand repo structure, test commands, and conventions)

## Usage

```text
User: Triage <PROJECT> bugs against this repo
User: Triage bugs from filter=<ID>
User: Triage project = <PROJECT> AND component = "<component>" AND status = New
User: Triage filter=<ID> and update JIRA with labels
User: Triage just <KEY>
```

## Implementation

### Step 1: Determine the Query, Target Repo, and Scope

**Query:**

1. If the user provides a JQL query, use it directly
2. If the user provides a filter ID, use `filter=<ID>` as the JQL
3. If the user names a component or project, construct JQL defaulting to **untriaged, unassigned** bugs and stories:
   `project = <PROJECT> AND component = "<component>" AND type in (Bug, Story) AND status in (New, Refinement, "To Do") AND assignee is EMPTY ORDER BY priority DESC`
4. If nothing specific is given, ask: "What JQL query or JIRA filter should I use?"

**Target repo:**

1. If the user names a repo, use it
2. If the workspace has a repo loaded, confirm: "I see `<repo>` loaded — should I triage bugs against this repo?"
3. If ambiguous, ask which repo to analyze against

**Repo state (read-only by default):**

Triage is read-only — never switch branches or modify files. Run `git fetch origin` and compare HEAD with `origin/main`. If behind, inform the user but proceed on the current HEAD. Only create a temporary branch (`git checkout -b ai-bug-fix-triage-<date> origin/main`) if the user explicitly asks. State which commit is being used.

### Step 2: Fetch Bugs and Manage Scope

Use the Atlassian MCP `searchJiraIssuesUsingJql` tool. Discover `cloudId` at runtime via `getAccessibleAtlassianResources`. Never hardcode cloud ID or site URL in output, comments, or reports.

```text
Tool: searchJiraIssuesUsingJql
Arguments:
  cloudId: <from getAccessibleAtlassianResources — never hardcode>
  jql: <constructed query>
  maxResults: 50
  responseContentFormat: "markdown"
  fields: ["summary", "description", "status", "issuetype", "priority",
           "labels", "components", "assignee", "created", "updated"]
```

**Fast path vs. interactive path:**

If the user provides a complete request (query + repo + exclusion criteria), proceed directly without stopping to ask questions. Only present scope options when genuinely needed:

- If results exceed one page (50 tickets), offer: narrow scope, work in batches per API page, or process all
- Track `nextPageToken` for iteration resume
- At the end of each batch, display a **progress summary** with cumulative counts:

```text
Processed 50/149+ | Relevant: 5 | AI-Fixable: 2 | Needs Human: 2 | Needs Info: 1 | Not Relevant: 45
Yield: 10% relevant | Continue? (next: 51-100) | "write back" | "stop"
```

When yield drops to zero for a full batch, recommend stopping. If the Not Relevant rate exceeds 80% in the first batch, suggest the user narrow their JQL (e.g., add keywords, restrict issue types, or use a more specific component) before continuing — this avoids burning through batches with low signal.

### Step 3: Filter Out Tickets Not Relevant to This Triage

Before analysis, filter out tickets that are managed elsewhere, irrelevant to the target repo, or already triaged.

**3a. Label-based relevance hints (soft signals)**

Scan each ticket's `labels` field before reading descriptions. Labels are **soft signals**, not definitive — always corroborate with the summary line before classifying as Not Relevant. If there is any doubt, read the description.

| Label pattern | Signal | Action |
|--------------|--------|--------|
| Automation labels (e.g., `auto-created`, `nightly-build`) | Auto-generated by CI/bots | Group together; check which repo's system failed |
| Repo or project name labels | Likely belongs to that repo | Confirm with summary before skipping |
| Technology/platform labels | Platform-specific scope | Narrow relevance, but target repo may still own the fix |
| Process/workflow labels | Organizational context | Check if they match the target repo's domain |

**3b. Skip already-triaged bugs (idempotency)**

Check each bug's labels for an existing classification label (`ai-fixable`, `ai-nonfixable`, `ai-needs-info`):

- **`ai-fixable` or `ai-nonfixable`**: Already triaged — skip by default.
- **`ai-needs-info`**: Always re-evaluate. Fetch full issue details via `getJiraIssue` to access comments and their timestamps. Check for replies posted after the original triage comment. If new information was provided, re-run the fixability analysis and update the classification. If no new info, skip.

Report: `Skipped: N tickets already classified (M ai-needs-info re-evaluated after new comments)`.

If the user explicitly requests re-triage (e.g., "re-triage everything"), process all tickets regardless of existing labels. Compare the new classification to the old and note any changes.

**3c. Ask about additional exclusion criteria** rather than assuming. Present observed patterns:

```text
I see the following patterns in the results:
  - N tickets with labels [auto-created, nightly-build] — are these handled by automation?
  - N tickets already assigned to someone — include or skip?
  - N tickets with status "Closed" or "Done" — skip these?
Which of these should I exclude?
```

If the user provides exclusion criteria upfront, apply them directly without asking.

**In the report**, summarize filters in one line:

```text
Excluded: 12 tickets (auto-created nightly failures per user request)
Skipped: 8 tickets (6 already classified; 2 ai-needs-info re-evaluated after new comments)
```

### Step 4: Analyze Each Bug for AI Fixability

For each bug remaining after filtering:

**4a. Read and understand the bug**

Extract: summary, full description, error messages/stack traces, affected files or components, repro steps, workarounds.

**4b. Check relevance to the target repo**

Check in this order (cheapest signals first):

1. **Labels + summary** — repo-name labels or `[org/repo-name]` summary prefixes identify ownership quickly; treat as strong hints, confirm before skipping (see Step 3a)
2. **File paths or script names** — do they match files in this repo?
3. **Repo references** — does the description mention this repo's project, or a different one?
4. **Error context** — does the error come from a CI job, container, or tool owned by this repo?
5. **Component and area** — does the described problem fall within what this repo is responsible for?

If the bug is clearly about a different repo or system, classify as **Not Relevant** with a brief note about the likely owner and move on. Do not search the codebase for bugs that aren't about this repo.

**4c. Search the target repo for related code**

Only for bugs that pass the relevance check:
- Search for file names, function names, script names mentioned in the bug
- Search for error messages or error patterns in the codebase
- Check `AGENTS.md` or `CLAUDE.md` for repo structure guidance
- Identify the specific files and lines where the issue likely originates

**4d. Apply the fixability rubric**

| Question | What to look for |
|----------|-----------------|
| **Root cause identifiable in this repo?** | Specific file, function, or config where the problem originates? If external system, upstream dep, or infrastructure — No. |
| **Clear code-level fix?** | Can the fix be expressed as a code change (config edit, logic fix, version bump, script fix)? Or does it need hardware access, infrastructure changes, upstream patches, or cross-team decisions? |
| **Fix verifiable?** | Does the repo have tests, linting, or CI checks covering this area? If no automated checks exist, can correctness be confirmed by code review (e.g., config fixes, documentation, straightforward logic changes)? Check `AGENTS.md` for test/verify commands. |

**4e. Classify**

| Classification | Criteria | Label |
|---------------|----------|-------|
| **AI-Fixable** | All 3 = Yes | `ai-fixable` |
| **Needs Human** | Any = No | `ai-nonfixable` |
| **Needs Info** | Description too vague to determine root cause | `ai-needs-info` |

**AI-Fixable** — also provide:
- **Fix approach**: 1-3 sentence description of what to change
- **Affected files**: Specific files to modify
- **Confidence**: High (exact fix identified) / Medium (likely fix, needs verification) / Low (plausible direction, uncertain)

**Needs Human** — briefly explain why (e.g., "requires upstream change", "needs infrastructure access", "cross-team architectural decision").

**Needs Info** — provide **actionable questions** that would unblock triage. Frame questions so anyone on the team can answer, not just the reporter. Examples:
- "What error output was produced when the build failed?"
- "Which version and variant reproduces this error?"
- "Can you provide the full stack trace from the CI job?"

### Step 5: Generate the Triage Report

Produce a markdown report with:

**Header**: Date, JQL used, target repo (commit/branch), counts (Fetched / Excluded / Skipped / Triaged).

**Summary table**: Counts by classification (AI-Fixable, Needs Human, Needs Info).

**AI-Fixable Bugs table**: Ordered by Priority > Confidence > Age. Columns: Key, Summary, Priority, Confidence, Fix Approach.

**Detailed Analysis** — one section per bug:
- All: Priority, Status, Age, Assignee, Classification, Reasoning (cite specific files/lines)
- AI-Fixable: add Fix Approach, Affected Files, Confidence
- Needs Human: add why AI cannot fix
- Needs Info: add Questions to unblock

**Iteration Status** (if batching): Progress summary with cumulative counts, yield rate per batch, and actionable next steps (same format as Step 2). When yield drops to zero for a full batch, recommend stopping.

### Step 6: JIRA Writeback (Optional)

Only perform if the user explicitly asks to "write back", "update JIRA", or "add labels". Only write labels and comments to tickets classified as **AI-Fixable**, **Needs Human**, or **Needs Info** — never label tickets classified as **Not Relevant**. Those tickets belong to other repos and adding labels would pollute their triage state.

**Idempotency check before writing:**

- **Labels**: If the bug already has the correct classification label (`ai-fixable`, `ai-nonfixable`, or `ai-needs-info`), skip the label update.
- **Labels changed**: If re-triaging produced a different classification, remove the old classification label and add the new one.
- **Comments**: If a comment containing "AI Triage Assessment" already exists, do not duplicate. If classification changed, add a new comment noting the update.

**Add labels** using `editJiraIssue`: preserve existing labels, append exactly one of `ai-fixable`, `ai-nonfixable`, or `ai-needs-info`. Do not add any additional meta-labels.

**Add triage comment** using `addCommentToJiraIssue` (markdown). Start with `**AI Triage Assessment**`, end with `_Generated by ai-bug-fix-triage skill_`. Content varies:

- **AI-Fixable**: Classification (with Confidence), Target Repo, Affected Files, Proposed Fix
- **Needs Info**: Classification, Target Repo, numbered list of questions to unblock
- **Needs Human**: no comment (label is sufficient)

## Error Handling

- **MCP not available**: Tell the user to configure and authenticate the Atlassian MCP server
- **Empty results**: Report no bugs found, suggest broadening the JQL
- **Repo not loaded**: Ask the user to open the target repo first
- **Dirty repo**: Not a problem — triage is read-only
- **Permission denied on writeback**: Skip that ticket, continue with the rest
- **Rate limiting**: Process writeback calls sequentially; back off on 429 responses
