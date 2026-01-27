# Edited by Claude Code
---
name: upload-slack-thread
description: Export Slack thread conversations to JIRA tickets as formatted markdown comments
---

## Name

jira:upload-slack-thread

## Synopsis

```
/jira:upload-slack-thread <slack-thread-url> [ticket-key] [--summary]
```

## Description

Export a Slack thread conversation to a JIRA ticket as a formatted markdown comment. This skill fetches messages from a Slack thread using the Slack MCP server and posts them as a comment to a JIRA ticket using the JIRA MCP server.

## Parameters

- `slack-thread-url`: Full Slack thread URL (required)
  - Format: `https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP`
- `ticket-key`: JIRA ticket key (optional)
  - Format: `PROJECT-NUMBER` (e.g., `JN-1234`, `AIPCC-7354`)
  - If not provided, will search thread messages for ticket references
- `--summary`: Include AI-generated summary before transcript (optional)

## Prerequisites

- Slack MCP server must be configured and accessible
- JIRA MCP server must be configured and accessible
- Appropriate permissions to read Slack channels and comment on JIRA tickets

## Implementation

### Step 1: Parse the Slack Thread URL

Extract components from the URL:

- URL pattern: `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TIMESTAMP>`
- Extract `channel_id` (e.g., `C09Q8MD1V0Q`)
- Convert timestamp: `p1769333522823869` → `1769333522.823869` (insert decimal before last 6 digits)

**Validation:**

- URL must match pattern `https://[^/]+\.slack\.com/archives/[A-Z0-9]+/p\d+`
- If invalid, display error: "Invalid Slack thread URL format. Expected: https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP"

### Step 2: Fetch Thread Messages via Slack MCP

Use `slack_get_replies` to fetch all messages in the thread:

- Parameters: `channel_id`, `thread_ts` (the converted timestamp)
- This returns all replies in the thread

**Handling:**

- If thread has >50 messages, truncate to first 50 and warn user
- Include the parent message (first message in thread)
- Preserve chronological order

### Step 3: Resolve User Display Names

For each unique `user_id` in the messages:

- The Slack MCP server typically includes user info in message responses
- If user info not available, use user_id as fallback display name
- Cache resolved names to avoid duplicate lookups

### Step 4: Determine JIRA Ticket Key

If `ticket-key` argument provided:

- Validate format matches `[A-Z]+-\d+`
- If invalid, display error with expected format

If `ticket-key` NOT provided:

- Search all message text for JIRA ticket pattern `[A-Z]+-\d+`
- Use first match found
- If no match found, ask user: "No JIRA ticket found in thread. Which ticket should this be posted to? (e.g., JN-1234)"

### Step 5: Format Messages as Markdown

Create markdown document with structure:

```markdown
# Slack Thread Export - {TICKET_KEY}

**Exported**: {ISO_TIMESTAMP}
**Slack Thread**: {ORIGINAL_URL}
**Channel**: #{CHANNEL_NAME}
**Messages**: {COUNT} {(truncated) if applicable}

## Summary (if --summary flag)

{AI-generated 1-2 paragraph summary of main topics, decisions, action items}

## Full Thread Transcript

### {USER_NAME} - {TIMESTAMP}

{MESSAGE_TEXT}

### {USER_NAME} - {TIMESTAMP}

{MESSAGE_TEXT}
```

**Message formatting:**

- Convert Slack timestamps to human-readable format
- Merge consecutive messages from same user (combine with double newline)
- Preserve code blocks and formatting
- Note attachments: "[Attachment: filename.ext]"

### Step 6: Post Comment to JIRA via JIRA MCP

Use `jira_add_comment` to post the formatted markdown:

- Parameters: `issue_key` (the ticket key), `body` (the markdown content)

**Error handling:**

- If ticket not found: "Unable to access ticket {KEY}. Verify the ticket exists and you have permission."
- If permission denied: "Permission denied. Ensure you have comment permission on {KEY}."

### Step 7: Confirm Success

Display success message:

```
✓ Successfully posted Slack thread to {TICKET_KEY}
  View: {JIRA_PROJECT_URL}/browse/{TICKET_KEY}
  Messages exported: {COUNT}
```

If truncated, also show:

```
  ⚠️ Thread truncated: showing {EXPORTED} of {TOTAL} messages
```

## Error Handling

- **Invalid URL format**: Display expected format with example
- **Slack MCP unavailable**: "Unable to connect to Slack MCP server. Verify MCP configuration."
- **JIRA MCP unavailable**: "Unable to connect to JIRA MCP server. Verify MCP configuration."
- **Empty thread**: "Thread has no messages to export."
- **Permission errors**: Provide specific guidance on required permissions

## Examples

### Basic Usage

```
User: /jira:upload-slack-thread https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 JN-1234
```

### Auto-detect Ticket

```
User: /jira:upload-slack-thread https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869
(Skill finds "JN-1234" mentioned in thread and uses it)
```

### With Summary

```
User: /jira:upload-slack-thread https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 JN-1234 --summary
(Includes AI summary before full transcript)
```
