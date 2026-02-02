---
name: jira-upload-slack-thread
description: Export Slack thread conversations to JIRA tickets as formatted markdown comments
allowed-tools: mcp__slack__conversations_replies mcp__mcp-atlassian__jira_add_comment
---

# jira:upload-slack-thread

Export a Slack thread conversation to a JIRA ticket as a formatted markdown comment.

## Synopsis

```
/jira:upload-slack-thread <slack-thread-url> [ticket-key] [--summary] [--summary-only]
```

## Parameters

- `slack-thread-url`: Full Slack thread URL (required)
  - Format: `https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP`
- `ticket-key`: JIRA ticket key (optional)
  - Format: `PROJECT-NUMBER` (e.g., `JN-1234`, `AIPCC-7354`)
  - If not provided, search thread messages for ticket references
- `--summary`: Include AI-generated summary before transcript (optional)
- `--summary-only`: Post only AI-generated summary without transcript (optional)
  - If both `--summary` and `--summary-only` are provided, `--summary-only` takes precedence

## Prerequisites

- Slack MCP server configured with valid authentication
- JIRA MCP server configured (`mcp__mcp-atlassian__jira_*` tools available)

## Implementation

### Step 1: Parse the Slack Thread URL

Extract components from the URL:

1. URL pattern: `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TIMESTAMP>`
2. Extract `channel_id` (e.g., `C09Q8MD1V0Q`)
3. Convert timestamp: `p1769333522823869` → `1769333522.823869` (insert decimal before last 6 digits)

**Validation:**
- URL must match pattern `https://[^/]+\.slack\.com/archives/[A-Z0-9]+/p\d+`
- If invalid: "Invalid Slack thread URL format. Expected: https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP"

### Step 2: Fetch Thread Messages via Slack MCP

Use the Slack MCP server to fetch thread messages:

```text
Tool: mcp__slack__conversations_replies
Parameters:
  - channel_id: {channel_id}
  - thread_ts: {converted_timestamp}
```

**Message processing:**
- Extract `user`, `text`, `ts`, `files` from each message
- If thread has >50 messages, truncate to first 50 and note in output
- Parent message (first) should be marked as thread starter

### Step 3: Resolve User Display Names

From the Slack MCP response:
- User display names are typically included in message responses
- If display_name available, use it; otherwise fallback to user_id
- Cache resolved names to avoid duplicate lookups

### Step 4: Determine JIRA Ticket Key

If `ticket-key` argument provided:
- Validate format matches `[A-Z]+-\d+`
- If invalid, display error with expected format

If `ticket-key` NOT provided:
- Search all message text for JIRA ticket pattern `[A-Z]+-\d+`
- Use first match found (chronological order)
- If no match: ask user "No JIRA ticket found in thread. Which ticket should this be posted to? (e.g., JN-1234)"

### Step 5: Format Messages as Markdown

Create markdown document based on flags:

**Flag behavior:**
- No flags: Full transcript only
- `--summary`: Summary + Full transcript
- `--summary-only`: Summary only (no transcript)

#### Format with `--summary-only`:

```markdown
# Slack Thread Export - {TICKET_KEY}

**Exported**: {ISO_TIMESTAMP}
**Slack Thread**: {ORIGINAL_URL}
**Channel**: #{CHANNEL_NAME}
**Messages**: {COUNT} (summary only)

## Summary

{AI-generated 1-2 paragraph summary of main topics, decisions, action items}

---
*Full thread transcript available at original Slack link above.*
```

#### Format with `--summary` (or no flag for transcript only):

```markdown
# Slack Thread Export - {TICKET_KEY}

**Exported**: {ISO_TIMESTAMP}
**Slack Thread**: {ORIGINAL_URL}
**Channel**: #{CHANNEL_NAME}
**Messages**: {COUNT} {(truncated) if applicable}

## Summary (if --summary flag)

{AI-generated 1-2 paragraph summary of main topics, decisions, action items}

## Full Thread Transcript

**[{TIMESTAMP}] {USER_NAME}:**
{MESSAGE_TEXT}

**[{TIMESTAMP}] {USER_NAME}:**
{MESSAGE_TEXT}
```

**Message formatting rules:**
- Convert Slack timestamps to `YYYY-MM-DD HH:MM:SS` format
- Merge consecutive messages from same user (combine text with double newline, preserve all attachments)
- Replace user mentions `<@U123>` with `**@username**`
- Replace channel mentions `<#C123|name>` with `**#name**`
- Clean URLs: remove `< >` wrapper, keep readable
- Add file attachment links: `📄 *File:* [filename.ext](url) (type)` (links to files in Slack, not embedded)
- Note reactions: `*Reactions:* :emoji: (count)`

### Step 6: Post Comment to JIRA via JIRA MCP

Use the JIRA MCP server to post the comment:

```
Tool: mcp__mcp-atlassian__jira_add_comment
Parameters:
  - issue_key: {TICKET_KEY}
  - comment: {formatted_markdown_content}
```

**Error handling:**
- Ticket not found: "Unable to access ticket {KEY}. Verify it exists and you have permission."
- Permission denied: "Permission denied. Ensure you have comment permission on {KEY}."

### Step 7: Confirm Success

Display success message:

```
✓ Successfully posted Slack thread to {TICKET_KEY}
  View: https://jounce.atlassian.net/browse/{TICKET_KEY}
  Messages exported: {COUNT}
```

If truncated:
```
  ⚠️ Thread truncated: showing {EXPORTED} of {TOTAL} messages
```

## Troubleshooting

| Issue | Solution |  
| --- | --- |  
| Slack MCP unavailable | Verify Slack MCP server is configured in Claude Code settings |  
| Authentication failed | Check Slack MCP server authentication tokens |  
| Invalid URL format | Display expected format with example |  
| JIRA MCP unavailable | Verify JIRA MCP server is configured |  
| Empty thread | "Thread has no messages to export." |  
| Permission errors | Provide specific guidance on required permissions |  

## Examples

### Basic Usage

```
/jira:upload-slack-thread https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 JN-1234
```

### Auto-detect Ticket

```
/jira:upload-slack-thread https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869
```
(Skill finds "JN-1234" mentioned in thread and uses it)

### With Summary

```
/jira:upload-slack-thread https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 JN-1234 --summary
```
(Includes AI summary before full transcript)

### Summary Only (no transcript)

```
/jira:upload-slack-thread https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 JN-1234 --summary-only
```
(Posts only the AI-generated summary, without the full thread transcript)
