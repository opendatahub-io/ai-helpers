---
name: jira-status-summary
description: >
  Update the Status Summary field on AIPCC Feature and Initiative tickets.
  Fetches child ticket activity via the jira-activity skill, generates a
  health-color summary (green/yellow/red), and writes it to Jira.
  Use when asked to update the status summary for a Jira ticket.
allowed-tools: Bash
user-invocable: true
---

# Jira Status Summary

Update the "Status Summary" custom field on an AIPCC Feature or Initiative
ticket with an AI-generated health-color summary.

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `JIRA_API_TOKEN` environment variable must be set with a valid API token for https://redhat.atlassian.net
- `JIRA_EMAIL` environment variable must be set with the email address associated with your Atlassian account
- The `jira-activity` skill must be installed (provides child ticket activity data)

## Usage

This skill takes a single ticket key as input and produces a formatted status
summary written to the Jira "Status Summary" custom field.

## Implementation

### Step 1: Determine the Ticket Key

1. If a ticket key is provided by the user, use it
2. Otherwise, search the conversation history for JIRA ticket references (e.g., "AIPCC-1234")
3. If no ticket is found in context, ask the user: "Which ticket should I update the Status Summary for? (e.g., AIPCC-1234)"

### Step 2: Fetch Child Ticket Activity

Run the fetch script from the `jira-activity` skill to gather activity data
for the ticket and its entire child hierarchy. Execute the script directly
(not via `python`) relative to the jira-activity skill directory:

```bash
./scripts/fetch_jira_activity.py <TICKET-KEY> --days 30
```

The script outputs JSON to stdout containing the complete hierarchy of issues
with levels, statuses, assignees, recent comments, and changelog entries.

Capture the full JSON output for analysis in the next step.

### Step 3: Analyze Activity and Generate Summary

Analyze the JSON output from Step 2 and determine:

#### Health Color

Assign exactly one of these colors:

- **green**: Work is progressing normally. Child tickets are moving through
  statuses, no significant blockers.
- **yellow**: Some concerns. Delays on key items, blocked tickets, slowing
  momentum, approaching deadline risks.
- **red**: Significant blockers. Most child tickets stalled, at risk of
  missing the due date, or critical path items are stuck.

#### Summary Text

Write a brief summary (2-4 sentences) for leadership consumption covering:

- Overall progress and momentum
- Key completions or milestones since last update
- Active risks, blockers, or dependencies (if any)
- What is coming next

The summary must be self-contained and understandable without reading the
child tickets. Do NOT include the date, color name, emoji, or disclaimer
in the summary text -- those are added automatically by the script.

### Step 4: Write to Jira

Run the write script located at `scripts/write_status_summary.py` relative
to this skill. Execute it directly (not via `python`) to invoke uv via the
shebang:

```bash
./scripts/write_status_summary.py <TICKET-KEY> --color <color> --summary "<summary text>"
```

The script will:
- Format the status string with today's date, color label, emoji, and AI disclaimer
- Convert to Atlassian Document Format (ADF)
- Write the value to the "Status Summary" custom field on the ticket
- Print a success or error message

### Step 5: Report Result

If the write succeeds, inform the user:

> Updated the Status Summary on <TICKET-KEY> with health color: <Color>.
> View: https://redhat.atlassian.net/browse/<TICKET-KEY>

If the write fails, display the error message and suggest checking credentials
and ticket permissions.

## Error Handling

- **Missing JIRA_API_TOKEN or JIRA_EMAIL**: Inform the user how to set them
- **jira-activity skill not found**: Tell the user the skill must be installed
- **Invalid Ticket Key**: Verify the ticket exists and is accessible
- **Permission Denied**: Check that the API token has permission to edit the ticket
- **Script Errors**: Display the stderr output from the script

## Examples

### Basic Usage
```text
User: Update the status summary for AIPCC-12345
Assistant: [Fetches activity, analyzes, writes summary to Jira]
```

### Context Detection
```text
User: We're reviewing AIPCC-12345. Can you update the status?
Assistant: [Detects ticket from context, fetches activity, writes summary]
```
