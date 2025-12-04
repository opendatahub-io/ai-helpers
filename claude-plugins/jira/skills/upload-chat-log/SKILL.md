---
name: upload-chat-log
description: Export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.
---

# Upload Chat Log to JIRA

Export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `JIRA_API_TOKEN` environment variable must be set with a valid API token for https://issues.redhat.com
- Appropriate JIRA permissions to add attachments to the target ticket

## Usage

This skill exports the current conversation as a formatted markdown document and uploads it as an attachment to a specified JIRA ticket.

## Implementation

### Step 1: Determine the Ticket Key

1. If a ticket key is provided by the user, use it
2. Otherwise, search the conversation history for JIRA ticket references (e.g., "AIPCC-1234", "working on PROJ-567")
3. If no ticket is found in context, ask the user: "Which JIRA ticket should I attach this chat log to? (e.g., AIPCC-1234)"

### Step 2: Format the Conversation with Summary and Full Transcript

Create a document with two main sections: Summary and Full Chat Log. Format the document as follows:

```markdown
# Chat Log Export - JIRA Ticket: [ticket-key]

**Exported**: [current timestamp]
**Ticket**: https://issues.redhat.com/browse/[ticket-key]

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
3. Store in `/tmp/claude/` directory (respects TMPDIR environment)

### Step 4: Upload to JIRA

1. Use the upload script located at `scripts/upload_chat_log.py` relative to this skill
2. Run the script directly (not via `python`) to invoke uv properly via the shebang:
   ```bash
   ./scripts/upload_chat_log.py <ticket-key> <file-path>
   ```
3. The script will:
   - Read the `JIRA_API_TOKEN` environment variable
   - Connect to https://issues.redhat.com
   - Upload the file as an attachment to the specified ticket
   - Return success or error messages

### Step 5: Confirm and Clean Up

1. If upload succeeds:
   - Inform the user: "Successfully uploaded chat log to {ticket-key} on https://issues.redhat.com"
   - Provide the direct link: `https://issues.redhat.com/browse/{ticket-key}`
2. If upload fails:
   - Display the error message from the script
   - Provide troubleshooting guidance (check token, permissions, ticket exists)
3. Delete the temporary file after upload attempt (success or failure)

## Error Handling

- **Missing JIRA_API_TOKEN**: Provide clear instructions on how to obtain and set the token
- **Invalid Ticket Key**: Verify the ticket exists and is accessible
- **Permission Denied**: Check that the API token has permission to add attachments
- **Script Not Found**: Verify the script exists at the expected path
- **Upload Failure**: Display the specific error and suggest checking network, credentials, and ticket accessibility

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