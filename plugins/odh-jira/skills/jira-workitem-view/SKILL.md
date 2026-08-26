---
name: jira-workitem-view
description: Retrieve and display full details of a Jira ticket. Fetches all fields and formats them for conversation context. Use when user needs ticket information or wants to examine a ticket.
allowed-tools: Bash, Skill
user-invocable: true
---

# Jira Workitem View

Retrieve and display comprehensive details of a Jira ticket using the `acli` CLI.

## Prerequisites

- `acli` must be installed and authenticated (`acli jira auth`)

## Implementation

### Step 1: Verify ACLi Setup

Before proceeding, verify that acli is installed and authenticated by invoking the `acli-setup-check` skill:

```text
/acli-setup-check
```

If the setup check fails, stop execution and guide the user to fix the issue.

### Step 2: Determine Ticket Key

1. If a ticket key is provided by the user (e.g., "AIPCC-1234"), use it
2. Otherwise, search the conversation history for Jira ticket references matching the pattern `[A-Z]+-\d+`
3. If no ticket is found, ask the user: "Which Jira ticket would you like to view?"

### Step 3: Fetch Full Ticket Details

Execute the command to retrieve all ticket fields:

# Fetch ticket details with validated key
acli jira workitem view "$TICKET_KEY" --fields '*all' --json
```

This returns a comprehensive JSON object containing all ticket fields, custom fields, and metadata.

### Step 4: Parse and Format Output

Parse the JSON output and extract the following fields for display:

#### Core Fields
- **Key**: Issue key (e.g., AIPCC-1234)
- **Summary**: Issue title
- **Type**: Issue type (Bug, Story, Epic, Feature, etc.)
- **Status**: Current status (To Do, In Progress, Done, etc.)
- **Priority**: Priority level
- **Project**: Project key and name

#### People
- **Assignee**: Current assignee (or "Unassigned")
- **Reporter**: Person who created the ticket
- **Creator**: Original creator (if different from reporter)

#### Dates
- **Created**: Creation timestamp
- **Updated**: Last update timestamp
- **Due Date**: Due date (if set)
- **Resolution Date**: When the ticket was resolved (if resolved)

#### Content
- **Description**: Convert from Atlassian Document Format (ADF) to plain text if needed. Display the first 500 characters with option to show full text.
- **Labels**: List of labels
- **Components**: List of components
- **Fix Version**: Target version (if set)

#### AIPCC Custom Fields (if applicable)
- **Status Summary** (customfield_10814): Leadership status update
- **Color Status** (customfield_10712): Red/Yellow/Green health indicator

#### Relationships
- **Parent**: Parent epic or feature (if set)
- **Child Issues**: Count and list of child issues
- **Links**: Related tickets (blocks, is blocked by, relates to, etc.)
- **Subtasks**: List of subtasks

#### Recent Activity
- **Last 3-5 Comments**: Show the most recent comments with author and timestamp

### Step 5: Display Results

Present the parsed information in a structured, human-readable format:

```
=== AIPCC-1234: Fix duplicate CI pipeline runs ===

Type: Bug
Status: In Progress → Done
Priority: Medium
Assignee: code-samurai
Reporter: super-picky-reviewer

Created: 2024-03-15
Updated: 2024-03-20
Due Date: 2024-03-25

Components: Wheel Package Index
Labels: ci, automation, bug-fix

Description:
  [First 500 chars of description...]
  (use --full to show complete description)

Status Summary (2024-03-20):
  Work progressing normally. CI fix merged and tested in staging.
  Ready for production rollout next sprint.
  Color Status: Green

Links:
  - Blocks: AIPCC-5678 (CI refactoring epic)
  - Relates to: RHOAIENG-910 (upstream fix)

Recent Comments (3):
  [2024-03-20] code-samurai: Fix verified in staging, ready to merge
  [2024-03-19] super-picky-reviewer: LGTM, approved for merge
  [2024-03-18] code-samurai: Initial fix implemented, testing locally

View in Jira: https://redhat.atlassian.net/browse/AIPCC-1234
```

### Step 6: Offer Additional Options

After displaying the summary, ask if the user wants:

1. Full description text
2. Complete comment history
3. Raw JSON output
4. Specific field details

### Optional: Store Context

Store the full ticket context in the conversation for later reference. This allows the user to ask follow-up questions about the ticket without re-fetching data.

## Error Handling

- **acli not found**: Delegate to `acli-setup-check` skill
- **Authentication failure**: Delegate to `acli-setup-check` skill
- **Invalid ticket key**: Verify format and suggest correction
- **Ticket not found**: Verify the ticket exists and user has access
- **Permission denied**: Inform user they may not have access to the ticket or project
- **Network errors**: Report error and suggest retrying

## Examples

### Basic Usage

```text
User: /jira-workitem-view AIPCC-1234
Assistant: [Fetches and displays formatted ticket details]
```

### Context Detection

```text
User: We need to look at AIPCC-1234 to understand the bug
Assistant: Let me fetch the details for AIPCC-1234...
[Displays ticket information]
```

### Show Full Description

```text
User: Show me the full description for AIPCC-1234
Assistant: [Fetches ticket and displays complete description text]
```

### View Specific Fields

```text
User: What's the status of AIPCC-1234?
Assistant: AIPCC-1234 is currently "In Progress" (updated 2024-03-20)
```
