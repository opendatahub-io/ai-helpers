---
name: agility-automation-finder
description: Identify automatable stories and opportunities for hands-off productivity by analyzing work items for automation potential, repeatability patterns, and toil reduction across delivery teams.
user-invocable: true
---

# Automation Opportunity Finder

Analyze a backlog, set of work items, or delivery workflow to identify stories and tasks that can be automated, partially automated, or eliminated through tooling. This skill helps delivery teams shift from manual execution toward hands-off productivity, freeing engineering capacity for higher-value work.

## When to Use

- During backlog grooming to flag automatable stories before sprint commitment
- When assessing a release train's work breakdown for toil reduction
- After a retrospective surfaces repeated manual effort
- When evaluating whether engineering capacity is spent on commodity work vs. differentiated delivery
- Before a release milestone to identify manual processes that could delay the train

## Input

Provide one or more of the following as context:

- **Work items**: A list of stories, tasks, or backlog items (structured or free-form text). Include titles, descriptions, acceptance criteria, and labels when available.
- **Workflow descriptions**: Narrative descriptions of recurring processes, manual steps, or operational procedures the team performs.
- **Sprint or release scope**: A snapshot of planned work for a sprint, PI, or release cycle.

Optionally include:

- **Current tooling**: Tools and platforms the team already uses (CI/CD, test frameworks, infrastructure-as-code, etc.)
- **Team capabilities**: Skills and automation experience available on the team.

## Instructions

### Step 1 - Understand the Work Context

Review the provided work items or workflow descriptions. For each item, identify:

- What the work accomplishes (outcome)
- How the work is currently performed (manual steps, human decisions, handoffs)
- How often this work recurs (one-time, per-sprint, per-release, continuous)
- Whether the work follows deterministic rules or requires judgment

### Step 2 - Classify Each Item

Evaluate every work item against these automation dimensions:

| Dimension | Question | Score |
|-----------|----------|-------|
| **Repeatability** | Does this work recur on a predictable cadence? | High / Medium / Low |
| **Rule-based logic** | Can the decision-making be codified into rules or scripts? | High / Medium / Low |
| **Data-driven** | Does the work operate on structured data with predictable inputs? | High / Medium / Low |
| **Toil indicator** | Is it manual, repetitive, and scales linearly with load? | Yes / No |
| **Integration surface** | Can existing tools or APIs handle part of this work? | High / Medium / Low |

Assign an overall **Automation Potential** rating:

- **High**: Three or more dimensions score High. Strong candidate for full automation.
- **Medium**: Mixed scores. Candidate for partial automation or assisted workflows.
- **Low**: Primarily judgment-driven, creative, or one-time work. Not a current automation target.

### Step 3 - Identify Automation Strategies

For items rated High or Medium, recommend a specific automation approach:

- **Full automation**: End-to-end scripting, pipeline integration, or bot-driven execution
- **Assisted automation**: Human-in-the-loop with automated preparation, validation, or reporting
- **Template/playbook**: Standardized runbook that reduces cognitive load without code
- **Elimination**: Work that can be removed entirely through architectural or process change

### Step 4 - Estimate Capacity Impact

For each recommended automation, estimate:

- **Current effort per occurrence**: How much engineer time this consumes today
- **Automation effort**: One-time investment to automate
- **Recurring savings**: Time saved per sprint or release cycle after automation
- **Payback horizon**: Number of cycles until the automation investment pays for itself

### Step 5 - Produce the Report

Generate the output following the **Output Template** below.

## Output Template

```markdown
# Automation Opportunity Analysis

## Executive Summary
[One-paragraph assessment of the overall automation landscape across the
provided work items. State how many items were analyzed, how many have
High/Medium/Low automation potential, and the estimated total capacity
that could be recovered.]

**Overall Risk Level**: [Critical | High | Moderate | Low]
(Risk of continuing without automation based on toil accumulation and delivery impact.)

## Key Findings

| # | Finding | Impact | Urgency |
|---|---------|--------|---------|
| 1 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |
| 2 | [description] | High/Medium/Low | Immediate/Near-term/Long-term |

## Automation Candidates

| Work Item | Automation Potential | Strategy | Current Effort | Recurring Savings | Payback |
|-----------|---------------------|----------|----------------|-------------------|---------|
| [item] | High/Medium | [approach] | [effort] | [savings] | [cycles] |

## Detailed Analysis

### High-Potential Candidates
[For each High-rated item: what it does, why it scores high, and the
specific automation approach with concrete next steps.]

### Medium-Potential Candidates
[For each Medium-rated item: what parts can be automated, what still
requires human judgment, and the recommended assisted workflow.]

### Low-Potential / Not Recommended
[Brief list of items that are not automation candidates and why.]

## Recommendations

| Priority | Action | Expected Outcome | Effort |
|----------|--------|-------------------|--------|
| 1 | [action] | [outcome] | High/Medium/Low |
| 2 | [action] | [outcome] | High/Medium/Low |

## Signals to Watch
- [Forward-looking indicators that suggest new automation opportunities]
- [Patterns that indicate toil is growing or automation is degrading]

## Data Gaps
- [Any missing information that would improve this analysis]
```

## Error Handling

- **No work items provided**: Ask the user to provide a backlog, list of stories, or workflow description
- **Insufficient detail**: If items lack descriptions or acceptance criteria, note which items could not be fully assessed and flag them in the Data Gaps section
- **Ambiguous scope**: If it is unclear whether the input represents a sprint, release, or ongoing backlog, ask the user to clarify the time horizon
- **No tooling context**: If the user does not provide current tooling information, produce the analysis without integration recommendations and note this in the Data Gaps section
