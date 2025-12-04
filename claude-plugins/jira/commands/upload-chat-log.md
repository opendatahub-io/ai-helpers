---
argument-hint: [ticket-key]
description: Export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.
---

## Name
jira:upload-chat-log

## Synopsis
```
/jira:upload-chat-log [ticket-key]
```

## Description

Export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.

## Implementation

Use the `jira:upload-chat-log` skill to export and upload the current chat conversation as a markdown file attachment to a JIRA ticket.

If a ticket key is provided as an argument (e.g., AIPCC-1234), pass it to the skill. Otherwise, let the skill determine the ticket from context or prompt the user.

Example usage:
- `/jira:upload-chat-log AIPCC-1234` - Upload to specific ticket
- `/jira:upload-chat-log` - Let skill find ticket from context or ask user
