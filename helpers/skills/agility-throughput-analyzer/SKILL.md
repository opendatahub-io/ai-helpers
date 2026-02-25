---
name: agility-throughput-analyzer
description: Analyze throughput at the team and individual engineer level to improve planning precision by identifying variance patterns, estimation accuracy, cycle time trends, and delivery predictability.
user-invocable: true
---

# Throughput Analyzer

Analyze delivery throughput data at team and individual engineer levels to improve planning precision. This skill identifies variance patterns, estimation accuracy gaps, cycle time bottlenecks, and WIP correlations that cause planning misses. The goal is to move from gut-feel estimation toward data-informed planning that accounts for actual delivery patterns.

## When to Use

- Before sprint or PI planning to calibrate capacity assumptions
- After a planning miss to understand where estimates diverged from actuals
- When teams consistently over- or under-commit
- To compare throughput patterns across teams for organizational insights
- When cycle times are growing and the root cause is unclear

## Input

Provide one or more of the following as context:

- **Completion data**: Stories, tasks, or work items completed over multiple sprints or periods. Include item identifiers, point values or sizes, start dates, and completion dates when available.
- **Sprint metrics**: Committed vs. delivered points or item counts per sprint, for at least 3 sprints (more data yields better trend analysis).
- **Cycle time data**: Time from work-started to work-completed for individual items.

Optionally include:

- **Individual attribution**: Which engineer completed which items (for individual-level analysis).
- **WIP snapshots**: Number of items in progress at any given time.
- **Item categories**: Story types (feature, bug, tech debt, spike) to analyze throughput by work type.
- **Team structure**: Team size, composition changes over the analysis period.

## Instructions

### Step 1 - Establish Baseline Metrics

From the provided data, calculate:

1. **Average throughput**: Mean items or points completed per period (sprint/week/month)
2. **Throughput range**: Min and max values across the analysis window
3. **Standard deviation**: Measure of throughput variability
4. **Coefficient of variation (CoV)**: Standard deviation divided by mean, as a percentage. This is the primary planning reliability indicator.

Interpret CoV:
- **< 20%**: Highly predictable. Team delivers consistently.
- **20-40%**: Moderate variability. Plan with buffer.
- **> 40%**: High variability. Estimates are unreliable without further analysis.

### Step 2 - Analyze Estimation Accuracy

If commitment vs. delivery data is available:

1. **Completion ratio**: Percentage of committed work delivered per sprint
2. **Bias direction**: Does the team consistently over-commit or under-commit?
3. **Accuracy trend**: Is estimation accuracy improving, stable, or degrading?
4. **Outlier identification**: Sprints with extreme over/under delivery and potential causes

### Step 3 - Cycle Time Analysis

If cycle time data is available:

1. **Median cycle time**: The typical time from start to completion
2. **85th percentile cycle time**: The "most items finish within X days" threshold
3. **Cycle time distribution**: Identify long-tail items that skew averages
4. **Aging WIP**: Items currently in progress that exceed the 85th percentile

### Step 4 - WIP Correlation

If WIP data is available:

1. **WIP vs. throughput correlation**: Does higher WIP increase or decrease throughput?
2. **Optimal WIP range**: The WIP level that maximizes throughput
3. **WIP limit recommendation**: Suggested per-person or per-team WIP cap

### Step 5 - Individual-Level Analysis

If individual attribution data is available:

1. **Individual throughput patterns**: Per-engineer completion rates
2. **Specialization effects**: Do certain engineers consistently handle specific work types?
3. **Load distribution**: Is throughput concentrated in a few engineers or spread evenly?
4. **Ramp-up patterns**: New team members and their throughput trajectory

Present individual data as **patterns and distributions**, not as performance rankings. The purpose is planning calibration, not evaluation.

### Step 6 - Produce the Report

Generate the output following the **Output Template** below.

## Output Template

```markdown
# Throughput Analysis

## Executive Summary
[One-paragraph assessment of overall delivery predictability. State the
analysis window, number of periods analyzed, and the primary finding
about planning reliability (CoV-based).]

**Overall Risk Level**: [Critical | High | Moderate | Low]
(Risk that current planning assumptions do not match actual throughput.)

## Key Findings

| # | Finding | Impact | Urgency |
|---|---------|--------|---------|
| 1 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |
| 2 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |

## Throughput Summary

| Metric | Value |
|--------|-------|
| Analysis window | [date range or sprint range] |
| Periods analyzed | [count] |
| Average throughput | [value per period] |
| Throughput range | [min - max] |
| Standard deviation | [value] |
| Coefficient of variation | [percentage] |
| Planning reliability | [High / Moderate / Low] |

## Estimation Accuracy

| Period | Committed | Delivered | Completion Ratio | Bias |
|--------|-----------|-----------|-----------------|------|
| [sprint/period] | [value] | [value] | [%] | Over/Under/On target |

**Accuracy trend**: [Improving / Stable / Degrading]
**Systematic bias**: [Tends to over-commit by X% / under-commit by X% / None]

## Detailed Analysis

### Throughput Trends
[Trend analysis with direction, inflection points, and potential causes.]

### Cycle Time Patterns
[If data available: distribution analysis, aging WIP, and bottleneck
identification.]

### WIP Impact
[If data available: correlation analysis and optimal WIP recommendations.]

### Work Type Breakdown
[If categorized data available: throughput differences by story type
and planning implications.]

## Recommendations

| Priority | Action | Expected Outcome | Effort |
|----------|--------|-------------------|--------|
| 1 | [action] | [outcome] | High/Medium/Low |
| 2 | [action] | [outcome] | High/Medium/Low |

## Planning Calibration

Based on this analysis, use these values for future planning:

- **Conservative estimate**: [value per period] (85% confidence)
- **Expected estimate**: [value per period] (50% confidence)
- **Optimistic estimate**: [value per period] (15% confidence)

## Signals to Watch
- [Indicators that throughput patterns are shifting]
- [Early warning signs for planning accuracy degradation]

## Data Gaps
- [Missing data that would improve this analysis]
```

## Error Handling

- **No throughput data provided**: Ask the user to provide sprint metrics, completion data, or delivery history
- **Fewer than 3 data points**: Produce the analysis but clearly warn that the sample size is too small for reliable trend analysis
- **Missing dates**: If cycle time analysis is requested but start/end dates are missing, skip cycle time sections and note the gap
- **Individual data sensitivity**: If individual attribution is provided, always present as patterns and distributions, never as rankings or comparisons
