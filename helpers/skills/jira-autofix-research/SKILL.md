---
name: jira-autofix-research
description: >-
  Research a Jira spike ticket with no associated repository.
  Investigates the topic and writes structured findings to the
  standard verdict file.
allowed-tools: Read Write Glob Grep Bash
---

# Skill: Research Spike Ticket

You are investigating a Jira spike ticket that has no associated code repository. Your job is to research the topic, gather findings, and write a structured verdict.

## Step 1: Parse the ticket

Read `.autofix-context/ticket.json`. Extract:

- The research question or investigation request
- Any constraints, deadlines, or scope boundaries
- Links, references, or prior art mentioned
- What the ticket opener expects as a deliverable

## Step 2: Investigate

Research the topic using available tools:

- Search for relevant documentation, prior issues, or existing solutions
- If upstream projects are involved, check their issue trackers and changelogs
- If architecture context files are available (`.triage-context/ARCHITECTURE.md`), read them for system context
- Synthesize findings into actionable recommendations

Focus on answering the ticket's question. Do not go on tangents.

## Step 3: Write verdict

Write `.autofix-verdict.json` to the workspace root:

```json
{
  "verdict": "research",
  "reason": "Investigated the feasibility of migrating to the new API version",
  "summary": "Migration is feasible with 3 breaking changes to address...",
  "files_changed": [],
  "risks": ["The new API drops support for legacy auth tokens"],
  "blockers": [],
  "self_review_issues_found": null,
  "self_review_issues_fixed": null,
  "lint_passed": null,
  "tests_passed": null,
  "upstream_consideration": "Upstream v2 API is stable as of release 3.4.0",
  "observations": [
    "Three breaking changes identified: auth token format, pagination response shape, error code enum",
    "Recommended approach: use the compatibility shim for 2 sprints while migrating callers",
    "Existing tests cover 80% of the affected API surface"
  ]
}
```

The `verdict` field must always be `"research"`. Put your detailed findings in `observations` as an array of strings -- each string should be a distinct finding or recommendation. Use `summary` for a concise 1-2 sentence overview. Use `risks` and `blockers` if the research uncovered obstacles. Use `upstream_consideration` if relevant upstream work was found.

Do not create any files other than the verdict. Do not modify any source code.
