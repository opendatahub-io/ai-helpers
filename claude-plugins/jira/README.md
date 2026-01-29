# JIRA Plugin

Tools and commands for interacting with JIRA resources, including sprint analysis and project management workflow automation.

## Commands

### `sprint-summary`

Generate comprehensive sprint summaries by analyzing JIRA sprint data, including issue breakdown, progress metrics, and team performance insights. Use this when you need to create detailed reports for sprint retrospectives, stakeholder updates, or performance tracking.

## Skills

### `upload-chat-log`

Export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.

### `upload-slack-thread`

Export Slack thread conversations to JIRA tickets as formatted markdown comments. Fetches thread messages via Slack MCP server and posts them as a comment to the specified JIRA ticket.

**Usage:**
```
/jira:upload-slack-thread <slack-thread-url> [ticket-key] [--summary] [--summary-only]
```

**Parameters:**
- `slack-thread-url` - Full Slack thread URL (required)
- `ticket-key` - JIRA ticket key like `JN-1234` (optional, auto-detected from thread if not provided)
- `--summary` - Include AI-generated summary before transcript (optional)
- `--summary-only` - Post only AI-generated summary without full transcript (optional)

**Features:**
- Parses Slack thread URLs and extracts channel/timestamp
- Fetches thread messages via Slack MCP (`mcp__slack__conversations_replies`)
- Auto-detects JIRA ticket keys from thread content
- Formats messages as clean markdown (user mentions, channel mentions, code blocks)
- Merges consecutive messages from the same user
- Posts to JIRA via MCP (`mcp__mcp-atlassian__jira_add_comment`)
- Truncates threads over 50 messages with warning

**Prerequisites:**
- Slack MCP server configured with authentication
- JIRA MCP server (mcp-atlassian) configured with authentication

## Installation

```bash
/plugin install jira@odh-ai-helpers
```