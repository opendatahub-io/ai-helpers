---
name: agility-priority-advisor
description: Recommend priority shifts to better align current work with periodic goals by analyzing priority discrepancies across strategic, feature, and story levels for quarterly, PI, or annual planning cycles.
user-invocable: true
---

# Priority Shift Advisor

Analyze current work priorities against periodic goals (quarterly objectives, PI goals, annual targets) to surface misalignments, over-investments, and coverage gaps. This skill helps agilists and delivery leads ensure that what teams are actually working on matches what the organization committed to delivering.

## When to Use

- At the start or midpoint of a planning cycle to validate alignment
- When strategic priorities shift and downstream impact needs assessment
- During PI planning to verify feature-to-strategy traceability
- When leadership raises concerns about delivery focus vs. stated goals
- After a missed milestone to identify where priorities diverged from plan

## Input

Provide one or more of the following as context:

- **Periodic goals**: Quarterly objectives, PI goals, annual targets, or strategic themes. Include goal descriptions, owners, and target dates when available.
- **Current work items**: Active backlog, in-flight features, or sprint content with their assigned priorities (P0/P1/P2, MoSCoW, or numeric ranking).
- **Goal period**: The time horizon for analysis (e.g., "Q1 2026", "PI 25.1", "FY2026 H1"). Defaults to the current quarter if not specified.

Optionally include:

- **Strategy-to-feature mapping**: How features trace back to strategic themes or initiatives.
- **Team assignments**: Which teams own which features or goals.
- **Completion status**: Current progress on goals and work items.

## Instructions

### Step 1 - Map the Goal Hierarchy

Build a mental model of the goal structure:

1. **Strategic level**: Organization-wide themes, OKRs, or annual commitments
2. **Feature level**: Planned capabilities, epics, or features that serve those strategies
3. **Execution level**: Stories, tasks, and sprint-level work that implement features

Identify any levels that are missing from the input and note them as data gaps.

### Step 2 - Detect Priority Discrepancies

Analyze alignment across levels by checking for:

| Discrepancy Type | Signal |
|-----------------|--------|
| **Orphan work** | Execution-level items with no clear link to any periodic goal |
| **Starved goals** | Goals with no active features or stories assigned to them |
| **Priority inversion** | Low-priority work consuming capacity while high-priority goals lack staffing |
| **Over-investment** | Disproportionate effort on goals that are already on track or low-impact |
| **Scope drift** | Work that was not part of the original goal set but has absorbed capacity |
| **Stale priorities** | Priorities that no longer reflect current organizational direction |

### Step 3 - Assess Goal Coverage

For each periodic goal, determine:

- **Coverage**: What percentage of the goal has active work in flight?
- **Velocity fit**: Based on current throughput, is the goal achievable within the period?
- **Risk level**: What is the likelihood of missing the goal given current trajectory?

Rate each goal:

- **On track**: Adequate coverage, velocity supports delivery
- **At risk**: Partial coverage or velocity gaps threaten delivery
- **Off track**: Insufficient work in flight to meet the goal
- **Exceeded**: More capacity allocated than the goal requires

### Step 4 - Recommend Priority Shifts

For each misalignment found, recommend a specific action:

- **Elevate**: Increase priority of underserved goal-aligned work
- **Deprioritize**: Reduce effort on over-invested or off-strategy work
- **Reassign**: Move work items to better-aligned teams or tracks
- **Defer**: Push non-critical work to a future period
- **Retire**: Remove goals or work that are no longer relevant
- **Escalate**: Flag decisions that require leadership input

### Step 5 - Produce the Report

Generate the output following the **Output Template** below.

## Output Template

```markdown
# Priority Alignment Analysis

## Executive Summary
[One-paragraph assessment of overall alignment between current work and
periodic goals. State the goal period analyzed, how many goals were
reviewed, and the overall alignment health: Strong / Moderate / Weak.]

**Overall Risk Level**: [Critical | High | Moderate | Low]
(Risk of missing periodic goals given current priority allocation.)

## Key Findings

| # | Finding | Impact | Urgency |
|---|---------|--------|---------|
| 1 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |
| 2 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |

## Goal Coverage Assessment

| Goal | Coverage | Velocity Fit | Status | Risk |
|------|----------|-------------|--------|------|
| [goal] | [%] | Sufficient/Insufficient | On track/At risk/Off track | High/Medium/Low |

## Priority Discrepancies

| Type | Affected Item | Current Priority | Recommended Priority | Rationale |
|------|--------------|-----------------|---------------------|-----------|
| [type] | [item] | [current] | [recommended] | [why] |

## Detailed Analysis

### Goals At Risk
[For each at-risk or off-track goal: what is missing, why it is
misaligned, and what needs to change.]

### Over-Invested Areas
[Work areas receiving disproportionate capacity relative to goal
importance or progress.]

### Orphaned Work
[Active work items with no clear connection to any periodic goal.]

## Recommendations

| Priority | Action | Expected Outcome | Effort |
|----------|--------|-------------------|--------|
| 1 | [action] | [outcome] | High/Medium/Low |
| 2 | [action] | [outcome] | High/Medium/Low |

## Signals to Watch
- [Indicators that priorities are drifting again]
- [Metrics to track alignment health over time]

## Data Gaps
- [Missing mappings, goals without owners, or items without priorities]
```

## Error Handling

- **No goals provided**: Ask the user to provide periodic goals, OKRs, or strategic objectives for the target period
- **No work items provided**: Ask the user to provide the current backlog, sprint content, or feature list with priorities
- **Missing goal period**: Default to the current quarter and note the assumption in the report
- **Incomplete traceability**: If strategy-to-feature mapping is missing, note which connections could not be verified and flag in Data Gaps
