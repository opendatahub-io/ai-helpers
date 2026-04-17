---
name: doc-pipeline
description: >
  Full pipeline orchestrator. Sequences doc-gather, doc-gap,
  doc-validate, doc-review, and doc-generate skills based on the
  requested pipeline mode.
argument-hint: "<JIRA-KEY> <gather|gap|validate|review|generate>"
model: claude-sonnet-4-5
effort: high
---

# doc-pipeline

Orchestrate documentation skills in dependency order based on the requested pipeline mode.

## Parse arguments

`$ARGUMENTS` contains:
1. **Jira key or PR URL**: the feature identifier (required)
2. **Mode**: one of `gather`, `gap`, `validate`, `review`, `generate` (required)

## Pipeline Modes

| Mode | Skills executed | Use case |
|---|---|---|
| `gather` | doc-gather | Collect context only |
| `gap` | doc-gather → doc-gap | Identify documentation gaps |
| `validate` | doc-gather → doc-validate | Validate existing docs against context |
| `review` | doc-gather → doc-validate → doc-review | Full validation and review of existing docs |
| `generate` | doc-gather → doc-gap → doc-generate → doc-validate → doc-review | Generate docs end-to-end |

## Execution Protocol

### Step 1: Validate inputs

- Confirm the Jira key or PR URL is provided
- Confirm the mode is one of the valid options
- Check that `configs/rhoai.yaml` exists

### Step 2: Execute skills in order

For each skill in the pipeline mode's sequence:

1. **Announce** the current phase to the caller
2. **Invoke** the skill using `/doc-<skill> <arguments>`
3. **Check** the skill output:
   - If the skill produced an output file, verify it exists
   - If the skill reported errors, decide whether to continue or halt
4. **Route** outputs to the next skill (via workspace files)

### Skill invocations by mode

#### `gather` mode
```
/doc-gather <JIRA-KEY>
```
Report: context package summary.

#### `gap` mode
```
/doc-gather <JIRA-KEY>
/doc-gap
```
Check: if gap report recommendation is `stop`, halt and report gaps to caller.
Report: gap report summary.

#### `validate` mode
```
/doc-gather <JIRA-KEY>
/doc-validate <docs-directory>
```
The docs directory is determined from the context package (the docs repo checkout path).
Report: validation findings summary.

#### `review` mode
```
/doc-gather <JIRA-KEY>
/doc-validate <docs-directory>
/doc-review <docs-directory>
```
Report: validation + review findings summary.

#### `generate` mode
```
/doc-gather <JIRA-KEY>
/doc-gap
```
**Gate**: Check gap report recommendation.
- If `stop`: halt, report insufficient context.
- If `gather-more`: warn, ask caller whether to proceed.
- If `proceed`: continue.

```
/doc-generate
/doc-validate workspace/generated-docs/
/doc-review workspace/generated-docs/
```
Report: generation report + validation + review summaries.

### Step 3: Final report

After all skills complete, produce a summary:

```
Pipeline: <mode>
Ticket: <JIRA-KEY>
Status: completed|halted

Phases:
  - doc-gather: completed (42 files, 85K tokens)
  - doc-gap: completed (recommendation: proceed, confidence: 0.82)
  - doc-generate: completed (3 modules, avg confidence: 0.85)
  - doc-validate: completed (0 high, 3 medium, 5 low findings)
  - doc-review: completed (confidence: 0.78)

Output files:
  - workspace/context-package.json
  - workspace/gap-report.json
  - workspace/generated-docs/
  - workspace/generation-report.json
  - workspace/validation-findings.json
  - workspace/review-findings.json
```

## Stop conditions

- **Halt**: Invalid mode argument
- **Halt**: Jira key/PR URL not provided
- **Halt**: Gap report recommends `stop` (in gap and generate modes)
- **Ask caller**: Gap report recommends `gather-more` (in generate mode)
- **Continue**: Individual validation/review findings (non-blocking)
- **Continue**: Missing optional tools (vale, lychee — validation runs partial)

## Post-pipeline options

After pipeline completes, offer the caller:
1. Post findings to a PR: `/doc-post <PR-URL>`
2. Re-run a specific phase with different parameters
3. View detailed findings from any phase
