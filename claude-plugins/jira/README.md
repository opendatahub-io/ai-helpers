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
/jira:upload-slack-thread <slack-thread-url> [ticket-key] [--summary] [--verbose]
```

## Installation

```bash
/plugin install jira@odh-ai-helpers
```