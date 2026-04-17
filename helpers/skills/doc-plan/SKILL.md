---
name: doc-plan
description: >
  STRAT-level documentation planning. Traverses a strategic initiative's
  child epics and stories to produce a systematic doc plan identifying
  what documentation is needed, what type, and at what priority.
argument-hint: "<STRAT-KEY|EPIC-KEY>"
model: claude-opus-4-6
effort: high
---

# doc-plan

Produce a documentation plan for a strategic initiative (STRAT) or epic by analyzing all child tickets for documentation impact.

## Parse arguments

`$ARGUMENTS` contains a Jira ticket key, typically a STRAT-level or epic-level ticket (e.g., `RHAISTRAT-1401` or `RHOAIENG-55000`).

## Step 1: Resolve the root ticket

Call the MCP tool to resolve the ticket:

```
mcp__mcp-atlassian__jira_get_issue(issue_key="<KEY>")
```

Extract:
- Summary, description, status
- Issue type (Initiative, Epic, Story)
- Fix versions
- Child tickets / linked tickets

## Step 2: Traverse child hierarchy

Resolve all child tickets recursively (up to 3 levels deep):

1. **STRAT/Initiative** → child Epics
2. **Epic** → child Stories/Tasks
3. **Story** → sub-tasks (if any)

For each ticket, resolve via MCP and extract:
- Key, summary, description, status, issue type
- Components
- Fix versions
- Labels

Limit: resolve up to 100 child tickets. If more exist, note the truncation.

## Step 3: Assess documentation impact

For each resolved child ticket, determine:

1. **Does this ticket affect documentation?**
   - Read the summary and description
   - Check if it introduces user-visible changes
   - Check components (documentation-relevant components vs internal)
   - Look for keywords: "API", "config", "parameter", "UI", "workflow", "deprecate"

2. **What type of documentation is needed?**
   - Map to: new_concept, new_procedure, new_reference, update_existing, release_note, deprecation_notice, none

3. **What priority?**
   - critical: mentioned in acceptance criteria, GA-blocking
   - high: significant user-facing change
   - medium: improvement, enhancement
   - low: minor change, edge case

4. **Dependencies?**
   - Which tickets share the same feature area?
   - Which tickets must be documented before this one?

## Step 4: Group and organize

Group documentation items by:
- Epic (parent grouping)
- Component (cross-cutting grouping)
- Priority (work ordering)

Identify:
- Tickets that can share documentation (combined into one doc)
- Tickets that need SME input
- Tickets where implementation is not yet complete (docs should wait)

## Step 5: Generate doc plan

Read `${CLAUDE_SKILL_DIR}/prompts/doc-plan.md` for the planning prompt.

Construct the plan combining:
- All ticket assessments
- Grouping and dependency analysis
- Coverage summary

## Step 6: Write output

Write the doc plan as markdown to stdout (for the caller to review).

Also write a structured version to `workspace/doc-plan.json` with the JSON format from the prompt template.

The markdown plan should include:

```markdown
# Documentation Plan: <STRAT summary>

**STRAT**: <KEY> — <summary>
**Generated**: <timestamp>
**Tickets analyzed**: <count>

## Summary

- **Tickets with doc impact**: N
- **Tickets without doc impact**: N
- **New concepts**: N
- **New procedures**: N
- **New references**: N
- **Updates to existing**: N
- **Release notes**: N

## Critical Priority

| Ticket | Summary | Doc Type | Modules | Dependencies |
|--------|---------|----------|---------|--------------|
| RHOAIENG-55490 | Model serving | new_procedure | proc_configure-model-serving | RHOAIENG-55489 |

## High Priority

...

## Medium Priority

...

## Low Priority

...

## No Documentation Impact

| Ticket | Summary | Reason |
|--------|---------|--------|
| RHOAIENG-55499 | Internal refactoring | No user-visible changes |

## Release Notes

| Ticket | Type | Summary |
|--------|------|---------|
| RHOAIENG-55490 | New feature | Model serving now supports custom runtimes |
```

## Output

Primary: Markdown doc plan (displayed to caller)
Secondary: `workspace/doc-plan.json`

## Stop conditions

- **Halt**: Root ticket not found
- **Halt**: MCP Jira tools not available
- **Warn**: Some child tickets fail to resolve (skip and note)
- **Warn**: Ticket hierarchy exceeds 100 tickets (truncate and note)
