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

### Steps 2-6: Detailed Implementation

See `references/guidelines.md` for detailed criteria covering:
- **Step 2**: Fetching bugs via Atlassian MCP, batch progress tracking, and fast-path vs. interactive-path logic
- **Step 3**: Filtering irrelevant tickets using label hints, idempotency checks, and exclusion criteria
- **Step 4**: Analyzing each bug for AI fixability (relevance check, code search, fixability rubric, classification)
- **Step 5**: Generating the triage report (header, summary table, AI-Fixable bugs table, detailed analysis)
- **Step 6**: Optional JIRA writeback (labels and triage comments with idempotency)

**Classifications at a glance:**

| Classification | Criteria | Label |
|---------------|----------|-------|
| **AI-Fixable** | Root cause identifiable, clear code fix, fix verifiable | `ai-fixable` |
| **Needs Human** | Any criterion fails | `ai-nonfixable` |
| **Needs Info** | Description too vague to determine root cause | `ai-needs-info` |

## Error Handling

- **MCP not available**: Tell the user to configure and authenticate the Atlassian MCP server
- **Empty results**: Report no bugs found, suggest broadening the JQL
- **Repo not loaded**: Ask the user to open the target repo first
- **Permission denied on writeback**: Skip that ticket, continue with the rest
- **Rate limiting**: Process writeback calls sequentially; back off on 429 responses
