---
name: agility-staffing-insights
description: Surface staffing insights based on skills, capacity, and velocity to identify coverage gaps, single-point-of-failure risks, overallocation, and team composition recommendations.
user-invocable: true
---

# Staffing Insights Analyzer

Analyze team composition, skill distribution, capacity allocation, and velocity patterns to surface staffing risks and recommendations. This skill helps agilists and delivery leads identify where teams are stretched thin, where critical knowledge is concentrated in too few people, and where capacity investments would have the highest return.

## When to Use

- During PI or quarterly planning to validate team capacity against commitments
- When a team's velocity drops and root causes are unclear
- Before a release milestone to assess whether staffing supports delivery targets
- When organizational changes (reorgs, attrition, new hires) impact team composition
- When cross-team dependencies create bottleneck risks

## Input

Provide one or more of the following as context:

- **Team roster**: Engineers and their roles, skill areas, or specializations. Can be a simple list of names and skills or a detailed skills matrix.
- **Capacity data**: Current allocation percentages, planned time off, part-time contributors, or split assignments across multiple teams or projects.
- **Velocity data**: Recent sprint velocity, story point completion, or throughput metrics per team or individual. Include at least 3 data points for trend analysis.

Optionally include:

- **Planned work**: Upcoming features, epics, or initiatives with skill requirements.
- **Dependency map**: Cross-team dependencies or shared ownership areas.
- **Attrition or hiring context**: Known departures, open positions, or onboarding timelines.

## Instructions

### Step 1 - Map Team Composition

Build a skills-to-people matrix from the provided data:

1. Identify each team member and their skill areas
2. Note primary vs. secondary skills (depth vs. breadth)
3. Map which product areas or components each person covers
4. Flag any skills or areas covered by a single person

### Step 2 - Assess Capacity Risks

Analyze capacity allocation looking for:

| Risk Pattern | Signal |
|-------------|--------|
| **Overallocation** | Engineer assigned to more work than their available capacity supports |
| **Single point of failure** | Critical skill or component area covered by only one person |
| **Fragmented allocation** | Engineer split across 3+ teams or workstreams, reducing effectiveness |
| **Capacity cliff** | Upcoming PTO, departure, or role change that will create a sudden gap |
| **Underutilization** | Capacity available but not aligned to priority work |

### Step 3 - Analyze Velocity Patterns

If velocity data is available:

1. Calculate velocity trends (improving, stable, declining) per team
2. Identify velocity variance (high variance indicates planning unpredictability)
3. Correlate velocity changes with staffing changes (new members, departures, splits)
4. Compare velocity per capita across teams to surface structural imbalances

### Step 4 - Identify Coverage Gaps

Cross-reference planned work against available skills:

- Which upcoming features require skills the team lacks?
- Which skill areas have depth (multiple people) vs. fragility (one person)?
- Where would a single departure create a delivery blocker?
- Are there skills the team needs to develop or hire for?

Calculate a **Bus Factor** for each critical skill area:
- **1 (Critical)**: Single person. Departure blocks delivery.
- **2 (Fragile)**: Two people. Manageable but risky under load.
- **3+ (Healthy)**: Sufficient coverage for sustained delivery.

### Step 5 - Produce the Report

Generate the output following the **Output Template** below.

## Output Template

```markdown
# Staffing Insights Analysis

## Executive Summary
[One-paragraph assessment of overall team health. State how many teams
or individuals were analyzed, the most critical risks found, and
whether current staffing supports planned delivery commitments.]

**Overall Risk Level**: [Critical | High | Moderate | Low]
(Risk that staffing gaps will impact delivery within the next 1-2 cycles.)

## Key Findings

| # | Finding | Impact | Urgency |
|---|---------|--------|---------|
| 1 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |
| 2 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |

## Skills Coverage Matrix

| Skill Area | People | Bus Factor | Risk Level | Notes |
|-----------|--------|------------|------------|-------|
| [area] | [names/count] | [1/2/3+] | Critical/Fragile/Healthy | [context] |

## Capacity Risk Assessment

| Risk Type | Affected | Severity | Timeframe | Mitigation |
|-----------|----------|----------|-----------|------------|
| [type] | [person/team] | High/Medium/Low | [when] | [action] |

## Detailed Analysis

### Critical Risks (Bus Factor = 1)
[For each single-point-of-failure: what skill or area is at risk,
who is the sole owner, and what breaks if they are unavailable.]

### Capacity Imbalances
[Teams or individuals who are overallocated, underutilized, or
fragmented across too many workstreams.]

### Velocity Trends
[If velocity data was provided: trend analysis, variance assessment,
and correlation with staffing patterns.]

## Recommendations

| Priority | Action | Expected Outcome | Effort |
|----------|--------|-------------------|--------|
| 1 | [action] | [outcome] | High/Medium/Low |
| 2 | [action] | [outcome] | High/Medium/Low |

## Signals to Watch
- [Leading indicators of staffing risk escalation]
- [Metrics to monitor for early warning]

## Data Gaps
- [Missing roster data, velocity history, or capacity details]
```

## Error Handling

- **No team data provided**: Ask the user to provide a team roster with skill areas or specializations
- **No velocity data**: Produce the analysis without velocity trends and note this as a data gap. Skills coverage and capacity analysis remain valid.
- **Partial data**: Analyze what is available, clearly label which sections are based on incomplete data, and list specifics in the Data Gaps section
- **Ambiguous skills**: If skill areas are too vague to assess coverage, ask the user to clarify the key technical domains for the team
