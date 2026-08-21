---
name: jira-status-summary
description: >
  Update the Status Summary and Color Status fields on AIPCC Feature and
  Initiative tickets. Fetches child ticket activity via the jira-activity
  skill, generates a brief summary and sets the red/yellow/green color status.
  Use when asked to update the status summary for a Jira ticket.
allowed-tools: Bash
user-invocable: true
---

# Jira Status Summary

Update the "Status Summary" and "Color Status" fields on an AIPCC Feature
or Initiative ticket with an AI-generated summary and health color.

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `acli` must be installed and authenticated (`acli jira auth`)
- `JIRA_API_TOKEN` environment variable must be set with a valid API token for https://redhat.atlassian.net
- `JIRA_EMAIL` environment variable must be set with the email address associated with your Atlassian account
- The `jira-activity` skill must be installed (provides child ticket activity data)

## Usage

This skill takes a single ticket key as input and writes a formatted status
summary to the Jira "Status Summary" field and sets the "Color Status"
dropdown.

If the user asks for a **dry run** (or uses the words "dry run", "preview",
"don't write", "show me first"), add `--dry-run` to the write command in
Step 5. This prints the formatted summary without writing to Jira, so the
user can review before committing.

## Implementation

### Step 1: Determine the Ticket Key

1. If a ticket key is provided by the user, use it
2. Otherwise, search the conversation history for JIRA ticket references matching the pattern `[A-Z]+-\d+`
3. If no ticket is found in context, ask the user: "Which ticket should I update the Status Summary for? (e.g., AIPCC-1234)"

### Step 2: Fetch Previous Status Summary and Color Status

Fetch the previous Status Summary and Color Status from the ticket:

```bash
acli jira workitem view <TICKET-KEY> -f 'customfield_10814,customfield_10712' --json
```

Parse the JSON output to extract:

- `customfield_10814`: the previous summary (rich-text / ADF content)
- `customfield_10712`: the previous color status ("Green", "Yellow", or
  "Red")

If either field is empty or unset, treat it as no previous value. Save
both outputs for use in Step 4 -- the previous color provides trending
context (e.g. improving from red to yellow).

If the command fails (e.g., due to permissions or network issues), continue
with Step 3 and generate the summary without prior context.

### Step 3: Fetch Child Ticket Activity

Run the fetch script from the `jira-activity` skill to gather activity data
for the ticket and its entire child hierarchy. Execute the script directly
(not via `python`) relative to the jira-activity skill directory:

```bash
./scripts/fetch_jira_activity.py <TICKET-KEY> --days 30
```

The script outputs JSON to stdout containing the complete hierarchy of issues
with levels, statuses, assignees, recent comments, and changelog entries.

Capture the full JSON output for analysis in the next step.

### Step 4: Analyze Activity and Generate Summary

Analyze the JSON output from Step 3 and determine:

#### Health Color

First, check the ticket's due date. If the due date is **more than 14 days
away**, assign **green** — early-stage features with ample time remaining
should not be penalized for low completion. Only override this to yellow or
red if child tickets have **explicit blockers** (status "Blocked", flagged
impediments, or unresolved dependency comments).

If the due date is 14 days away or fewer (or no due date is set), assign a
color based on progress and risk:

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
- Follow-up on items from the previous status (if a previous summary was
  retrieved in Step 2): address open questions, note whether raised risks
  or blockers have been resolved, and flag anything that was mentioned
  previously but still has no progress

For **yellow** or **red** items, the summary must also include a description
of the issue and a "path to green" (e.g. move dates, escalation, dependency
resolution).

The summary must be self-contained and understandable without reading the
child tickets. Do NOT include the date, color name, emoji, or disclaimer
in the summary text -- those are added automatically by the script.

### Step 5: Write to Jira

Run the write script located at `scripts/write_status_summary.py` relative
to this skill. Execute it directly (not via `python`) to invoke uv via the
shebang:

```bash
./scripts/write_status_summary.py <TICKET-KEY> --color <color> --summary "<summary text>"
# Or for dry run:
./scripts/write_status_summary.py <TICKET-KEY> --color <color> --summary "<summary text>" --dry-run
```

The script will:
- Set the "Color Status" dropdown field (red/yellow/green) on the ticket
- Format the status string with today's date and AI disclaimer (no color
  in the text -- color is tracked in the separate "Color Status" field)
- Convert to Atlassian Document Format (ADF)
- Write both fields to the ticket in a single API call
- Print a success or error message

### Step 6: Report Result

**Normal run:** If the write succeeds, inform the user:

> Updated the Status Summary and Color Status (<Color>) on <TICKET-KEY>.
> View: https://redhat.atlassian.net/browse/<TICKET-KEY>

**Dry run:** Show the formatted summary and ask:

> Here is the status summary that would be written to <TICKET-KEY>:
>
> (show the output)
>
> Would you like me to write this to Jira?

If the user confirms, re-run Step 5 without `--dry-run`.

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
