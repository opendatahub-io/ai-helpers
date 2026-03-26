---
name: aipcc-package-onboarding-status
description: Analyze AIPCC package onboarding backlog to identify stale tickets, workflow anomalies, and items requiring human intervention.
allowed-tools: Bash
user-invocable: true
---

# AIPCC Package Onboarding Backlog Status

Analyze the AIPCC package onboarding backlog to identify stale tickets, workflow anomalies, and items that require human intervention. Produces a structured markdown report suitable for backlog review meetings.

## Prerequisites

- Python 3 must be installed and available in PATH
- `acli` (Atlassian CLI) must be installed and authenticated (run `acli jira auth` first)
- Appropriate JIRA permissions to read AIPCC project tickets

## Context: Package Onboarding Workflow

The AIPCC package onboarding system is an automated pipeline that processes package requests through these phases:

1. **Not Started** (New/To Do) - Epic created but automation hasn't started
2. **Refinement** - Automation has picked up the ticket (`package-automation-onboarded` label)
3. **In Progress** - Pipeline is executing. Sub-phases include:
   - **Automation Running** - Pipeline jobs executing
   - **Build Failed (awaiting investigation)** - Self-service build failed, no builder story yet
   - **Builder Onboarding** - Builder story created but not yet resolved
   - **Builder Done (awaiting pipeline/build)** - Builder story closed, waiting for pipeline MR
   - **License Blocked** - License is incompatible with redistribution
   - **In Test Repo (awaiting QA)** - Package built and in test repo, AutoQA not yet passed
   - **QA Failed** - AutoQA tests are failing
   - **QA Passed (stories pending)** - AutoQA passed but some child stories are still open
   - **Ready for Review (pending lifecycle)** - All stories closed, autoqa passed, awaiting lifecycle job
   - **Production (pending closure)** - Package in production repo, epic should be closing
4. **Review** - All child stories closed, package in test repo, autoqa passed. Awaiting production promotion.
5. **Closed** - Package is in the production repository

### Child Story Types

Each Epic may have these child stories (created by automation):

| Story Type | Summary Pattern | Labels | Notes |
|---|---|---|---|
| **Builder** | "Onboard {pkg} into the AIPCC Builder" | `package-builder-onboarded` | Only on failure path |
| **Pipeline** | "Add {pkg} into the RHAI pipeline onboarding" | `package-pipeline-onboarded` | Both paths |
| **QE Testing** | "QE Testing for package {pkg}" | - | Both paths |
| **Probe Test** | "Probe test..." | `package-probe-tests-created` | Only on failure path |

### Lifecycle Automation Rules

A scheduled pipeline runs every 3 hours and manages transitions:

- **Epic -> Review**: Requires ALL of: status=In Progress, `package-in-test-repo`, `package-automation-onboarded`, `package-autoqa-passed`, ALL child stories Closed
- **Epic -> Closed**: Requires: status=Review, `package-automation-onboarded`, `package-autoqa-passed`, package verified in production repo

## Implementation

### Step 1: Determine Parameters

1. If the user specifies a staleness threshold in days, use it (default: 7)
2. If the user specifies a custom JQL query, use it
3. Otherwise use the default JQL: `project = aipcc and labels = package and issuetype = Epic and status != Closed order by key desc`

### Step 2: Fetch Backlog Data

Run the fetch script located at `scripts/fetch_backlog_status.py` relative to this skill:

```bash
./scripts/fetch_backlog_status.py [--days N] [--jql "JQL"]
```

The script outputs JSON to stdout containing every open Epic with its children, detected anomalies, and workflow phase. It also prints progress to stderr.

### Step 3: Interpret the JSON into a Backlog Status Report

Analyze the JSON output and produce a report using the template below. Use your knowledge of the workflow (documented above) to provide actionable insights.

#### Report Template

```markdown
# AIPCC Package Onboarding Backlog Status

**Generated:** {date}
**Epics Analyzed:** {total}
**Staleness Threshold:** {days} days

## Executive Summary

{1-3 sentences summarizing the overall health of the backlog}

**Quick Stats:**
- {X} epics require human intervention (high severity anomalies)
- {X} epics are progressing normally
- {X} epics are stale (no activity in {N}+ days)

## Phase Distribution

| Phase | Count | Epics |
|---|---|---|
| {phase} | {count} | {EPIC-1, EPIC-2, ...} |
| ... | ... | ... |

## Anomalies Requiring Attention

### Critical (High Severity)

Items that are stuck and likely need immediate human intervention.

#### {EPIC-KEY}: {package-name}
- **Status:** {status} | **Phase:** {phase}
- **Last Updated:** {date} ({N} days ago)
- **Issue:** {anomaly message}
- **Recommended Action:** {specific action to take}

### Warnings (Medium Severity)

Items showing workflow inconsistencies or moderate staleness.

#### {EPIC-KEY}: {package-name}
- **Status:** {status} | **Phase:** {phase}
- **Issue:** {anomaly message}
- **Children:** {summary of child story states}

### Informational (Low / Info Severity)

Items worth noting but not urgent.

- **{EPIC-KEY}** ({package-name}): {brief anomaly description}

## Stale Epics

Epics with no updates beyond the staleness threshold, grouped by phase.

### {Phase Name} ({count})

| Epic | Package | Last Updated | Days Stale | Anomalies |
|---|---|---|---|---|
| {key} | {name} | {date} | {days} | {count} |

## Healthy Epics

Epics progressing normally with no anomalies.

| Epic | Package | Phase | Last Updated |
|---|---|---|---|
| {key} | {name} | {phase} | {date} |

## Recommendations

{Bulleted list of high-level recommendations based on patterns seen across the backlog. Examples:}
- {N epics are stuck in "Build Failed" with no builder story — the failure-analysis pipeline may need attention}
- {N epics have autoqa_passed but open QE stories — automation may not be closing these stories}
- {Lifecycle job may not be running — N epics should have transitioned to Review}
```

### Interpretation Guidelines

When generating the report:

1. **Group anomalies by severity** — high severity items go first as they block automation
2. **Identify systemic patterns** — if the same anomaly type appears across many epics, flag it as a potential automation bug rather than listing each one individually
3. **Provide specific actions** — don't just describe the problem, suggest what the human should do:
   - "Manually close QE story AIPCC-XXXX to unblock lifecycle transition"
   - "Check if lifecycle scheduled pipeline is running"
   - "Review and merge the builder MR, then re-run the onboarding pipeline"
4. **Call out lifecycle blockers** — the most common human intervention needed is when a Story is open and blocking the Epic from auto-transitioning to Review. Always highlight these prominently.
5. **Flag duplicate stories** — when the pipeline ran multiple times, it may create duplicate stories. One may be Closed and one open, preventing the lifecycle job from closing the Epic.
6. **Detect stale build failures** — epics with `package-build-failed` and no children (or no builder story) that haven't been updated in {stale_days} are likely stuck and need someone to re-run the pipeline or investigate.

## Error Handling

- **acli not found or not authenticated**: Instruct the user to install acli and run `acli jira auth`
- **No Epics Found**: Report that the backlog is empty or the JQL returned no results
- **Script Timeout**: The script may take several minutes for large backlogs (50+ epics). Inform the user.
- **JIRA Permission Errors**: Note which epics failed and report on the ones that succeeded

## Examples

### Basic Usage
```text
User: What's the status of the package onboarding backlog?
Assistant: [Runs fetch script, produces backlog status report]
```

### Custom Staleness Threshold
```text
User: Show me stale package onboarding tickets, anything not updated in 14 days
Assistant: [Runs fetch script with --days 14, produces report]
```

### Filtered Query
```text
User: Check the status of AIPCC-12101 package onboarding
Assistant: [Runs fetch script with --jql filtering to that epic, produces report]
```
