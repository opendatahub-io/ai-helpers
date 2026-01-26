---
name: upload-slack-thread
description: Export Slack thread conversations to JIRA tickets as formatted markdown comments
---

# Upload Slack Thread to JIRA

## Overview

This skill fetches a Slack thread conversation via Slack MCP server and uploads it as a formatted markdown comment to a JIRA ticket using the JIRA MCP server.

## Prerequisites

1. **Slack MCP Server** configured with:
   - `SLACK_XOXC_TOKEN`
   - `SLACK_XOXD_TOKEN`

2. **JIRA MCP Server** configured with access to your JIRA instance

3. **Environment Variables**:
   ```bash
   export JIRA_PROJECT_URL="https://yourinstance.atlassian.net/"
   export JIRA_API_TOKEN="your-api-token"
   ```

## Usage

### Basic Usage

```bash
# With explicit ticket key
uv run claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py \
  "https://workspace.slack.com/archives/C09Q8MD1V0Q/p1769333522823869" \
  JN-1234

# Auto-detect ticket from thread
uv run claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py \
  "https://workspace.slack.com/archives/C09Q8MD1V0Q/p1769333522823869"

# With AI summary
uv run claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py \
  "https://workspace.slack.com/archives/C09Q8MD1V0Q/p1769333522823869" \
  JN-1234 \
  --summary

# Verbose mode for debugging
uv run claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py \
  "https://workspace.slack.com/archives/C09Q8MD1V0Q/p1769333522823869" \
  JN-1234 \
  --verbose
```

## Features

- **URL Parsing**: Validates and parses Slack thread URLs
- **Message Fetching**: Retrieves all thread messages via Slack MCP
- **User Resolution**: Converts Slack user IDs to display names
- **Message Merging**: Consolidates consecutive messages from same user
- **Auto-Detection**: Searches thread for JIRA ticket references
- **AI Summary**: Optional AI-generated summary (1-2 paragraphs)
- **Truncation Handling**: Limits to 50 messages with clear warnings
- **Markdown Formatting**: Formats messages as readable markdown
- **JIRA Upload**: Posts as comment to specified ticket

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `slack_thread_url` | Yes | Slack thread URL (format: `https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP`) |
| `ticket_key` | No | JIRA ticket key (format: `[A-Z]+-\d+`). Auto-detected if not provided. |
| `--summary`, `-s` | No | Enable AI-generated thread summary |
| `--verbose`, `-v` | No | Enable verbose logging for debugging |

## Output Format

The skill generates markdown with the following structure:

```markdown
# Slack Thread Export - TICKET-KEY

**Exported**: 2026-01-26T10:30:00Z
**Slack Thread**: https://workspace.slack.com/archives/...
**Channel**: #channel-name

## Summary (if --summary enabled)

AI-generated summary covering main topics, decisions, and action items...

## Full Thread Transcript

### User Name - 2026-01-26 10:15:00
Message content here...

### User Name - 2026-01-26 10:20:00
Another message...
```

## Error Handling

The skill validates inputs and provides actionable error messages:

- **Invalid URL**: Clear format requirements
- **Invalid Ticket Key**: Expected pattern examples
- **MCP Server Unavailable**: Configuration instructions
- **Permission Denied**: Access requirement details
- **Rate Limiting**: Retry suggestions

All errors output to stderr with exit codes per contract.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments or input validation error |
| 2 | Slack MCP server connection error |
| 3 | JIRA MCP server connection error |
| 4 | Permission denied or authentication error |
| 5 | Resource not found (thread or ticket) |

## Performance

- URL parsing: <200ms
- Slack API calls: <10s
- JIRA comment post: <5s
- Total workflow: <30s (for threads up to 50 messages)

## Limitations

- **Message Limit**: Truncates at 50 messages with warning
- **URL Format**: Supports standard Slack thread URLs only
- **MCP Dependency**: Requires both Slack and JIRA MCP servers

## Implementation

See the quickstart guide in `specs/001-jira-upload-slack-thread/quickstart.md` for detailed usage examples and troubleshooting.

## Testing

```bash
# Run contract tests
pytest tests/contract/test_upload_slack_thread_contract.py

# Run integration tests
pytest tests/integration/

# Run unit tests
pytest tests/unit/

# Run all tests
pytest tests/
```
