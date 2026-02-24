---
name: jira-activity
description: Summarize Jira ticket activity, including child tickets, to detect stale tickets in the backlog. Use when user asks to review one or more Jira tickets to determine if they are being worked on.
allowed-tools: Bash
user-invocable: true
---

# Jira Activity Summary

Analyze a Jira ticket and its child tickets to produce a staleness report. Useful for triaging Features and Initiatives to determine if they are actively being worked on, slowing down, or dormant.

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `JIRA_API_TOKEN` environment variable must be set with a valid API token for https://issues.redhat.com
- Appropriate JIRA permissions to read the target ticket and its children

## Usage

This skill fetches activity data for a Jira ticket and its entire descendant hierarchy (Initiative → Epic → Stories/Tasks), then interprets the results into a staleness report.

## Implementation

### Step 1: Determine the Ticket Key

1. If a ticket key is provided by the user, use it
2. Otherwise, search the conversation history for JIRA ticket references (e.g., "AIPCC-1234", "RHOAIENG-567")
3. If no ticket is found in context, ask the user: "Which JIRA ticket should I analyze? (e.g., RHOAIENG-1234)"

Optionally the user may specify a `--days N` flag to control the lookback window (default: 30 days).

### Step 2: Fetch Activity Data

Run the fetch script located at `scripts/fetch_jira_activity.py` relative to this skill. Execute it directly (not via `python`) to invoke uv via the shebang:

```bash
./scripts/fetch_jira_activity.py <TICKET-KEY> [--days N]
```

The script outputs JSON to stdout containing the complete hierarchy of issues with levels (0=root, 1=child, 2=grandchild, etc.) including statuses, assignees, recent comments, and changelog entries.

### Step 3: Interpret the JSON into a Staleness Report

Analyze the JSON output and produce a report with the following sections:

#### Overall Staleness Assessment

Assign one of these labels based on the activity patterns:

- **Active**: Regular status changes, comments, or updates within the lookback window
- **Moderate**: Some activity but gaps or only partial child ticket movement
- **Stale**: Little to no meaningful activity; most child tickets idle
- **Dormant**: No activity at all across parent and children during the lookback window

#### Hierarchy Overview

Present the complete hierarchy structure showing:
- Root issue (level 0) - typically Initiative/Feature
- Child issues (level 1) - typically Epics
- Grandchild issues (level 2+) - typically Stories/Tasks

#### Issue Breakdown by Level

For each level in the hierarchy, summarize:
- Total count and types of issues
- Status distribution (New, In Progress, Closed, etc.)
- Recent activity patterns
- Individual staleness signals (active/idle)

For key issues with significant activity, include:
- Key, summary, status, assignee, last updated
- Recent comments or status transitions

Present as a hierarchical summary or grouped by level.

#### Key Takeaways

- Cross-level activity analysis (e.g., "Initiative appears stale but Epic has active Stories")
- Breakdown of active vs idle work by hierarchy level
- Any blockers or stalled tracks worth attention
- Recommendations for triage focus (e.g., "5 of 7 Stories completed recently, Epic shows strong momentum despite Initiative-level inactivity")

## Error Handling

- **Missing JIRA_API_TOKEN**: Inform the user how to obtain and set the token
- **Invalid Ticket Key**: Verify the ticket exists and is accessible
- **Permission Denied**: Check that the API token has permission to view the ticket
- **Script Not Found**: Verify the script exists at the expected path
- **No Children Found**: Report on the parent ticket only and note that no child tickets were found

## Examples

### Basic Usage
```text
User: Check activity on RHOAIENG-1234
Assistant: [Runs fetch script, analyzes JSON, produces staleness report]
```

### Custom Lookback Window
```text
User: Is AIPCC-500 stale? Look back 60 days.
Assistant: [Runs fetch script with --days 60, produces report]
```

### Context Detection
```text
User: We're triaging RHOAIENG-9999. How active is it?
Assistant: [Detects ticket from context, runs analysis]
```
