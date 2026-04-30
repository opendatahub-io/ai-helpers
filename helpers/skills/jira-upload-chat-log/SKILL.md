---
name: jira-upload-chat-log
description: Use this skill to export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.
allowed-tools: Skill, AskUserQuestion
user-invocable: true
---

# Upload Chat Log to JIRA

Export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.

## Prerequisites

- The `jira-workitem-attach` skill must be installed
- `JIRA_API_TOKEN` environment variable must be set with a valid API token for https://redhat.atlassian.net
- `JIRA_EMAIL` environment variable must be set with the email address associated with your Atlassian account
- Appropriate JIRA permissions to add attachments to the target ticket

## Usage

This skill exports the current conversation as a formatted markdown document and uploads it as an attachment to a specified JIRA ticket.

## Implementation

### Step 1: Determine the Ticket Key

1. If a ticket key is provided by the user, use it
2. Otherwise, search the conversation history for JIRA ticket references matching the pattern `[A-Z]+-\d+`
3. If no ticket is found in context, ask the user: "Which JIRA ticket should I attach this chat log to? (e.g., AIPCC-1234)"

### Step 2: Format the Conversation with Summary and Full Transcript

Create a document with two main sections: Summary and Full Chat Log. Format the document as follows:

```markdown
# Chat Log Export - JIRA Ticket: [ticket-key]

**Exported**: [current timestamp]
**Ticket**: https://redhat.atlassian.net/browse/[ticket-key]

---

## Summary

[Provide a concise summary of the conversation including:
- Main topic/task discussed
- Key decisions made
- Files created/modified
- Important outcomes or next steps
- 3-5 paragraphs maximum]

---

## Full Chat Transcript

[Export the complete conversation transcript in the same format as the `/export` command:
- All user messages and assistant responses
- All tool calls and their results
- Code blocks, thinking blocks, and system messages
- Timestamps and metadata
- The full, unabridged conversation from start to finish]
```

The summary should be human-readable and highlight key points. The full transcript should be comprehensive for detailed review.

### Step 3: Save to Temporary File

1. Create a temporary file with a descriptive name: `chat-log-{ticket-key}-{timestamp}.md`
2. Write the formatted conversation to this file
3. Store in the system temporary directory (e.g., `/tmp` on Linux, `/private/tmp` on macOS, or use `mktemp` to create in the appropriate location)

### Step 4: Upload to JIRA

Invoke the `jira-workitem-attach` skill to upload the file:

```
/jira-workitem-attach <ticket-key> <file-path>
```

The skill will:
- Verify environment variables (JIRA_API_TOKEN, JIRA_EMAIL) are set
- Verify the ticket exists and is accessible
- Upload the file as an attachment
- Display success message with attachment details
- Handle all error cases (authentication, permissions, file size, etc.)

### Step 5: Confirm and Clean Up

1. If upload succeeds:
   - Inform the user: "Successfully uploaded chat log to {ticket-key}"
   - The `jira-workitem-attach` skill will provide the direct ticket link
2. If upload fails:
   - The `jira-workitem-attach` skill will display the error and troubleshooting guidance
3. Delete the temporary file after upload attempt (success or failure)

## Error Handling

- **Missing jira-workitem-attach skill**: Inform user that the skill must be installed
- **Chat export failure**: Check conversation history is available
- **File creation failure**: Verify temp directory is writable
- **Upload errors**: Delegated to the `jira-workitem-attach` skill (handles authentication, permissions, file size, etc.)

## Examples

### Basic Usage
```
User: Upload this chat to AIPCC-7354
Assistant: [Skill creates formatted chat log and uploads to AIPCC-7354]
```

### No Ticket Specified
```
User: Upload this conversation to JIRA
Assistant: Which JIRA ticket should I attach this chat log to? (e.g., AIPCC-1234)
User: RHEL-9876
Assistant: [Skill uploads to RHEL-9876]
```

### Context Detection
```
User: We're working on AIPCC-7354. Can you upload our conversation?
Assistant: [Skill detects AIPCC-7354 from context and uploads automatically]
```