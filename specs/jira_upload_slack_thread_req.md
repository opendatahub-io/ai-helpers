# Feature Requirement: jira-upload-slack-thread

## Overview

Create a new Claude Code skill that fetches a Slack thread and uploads it as a markdown file attachment to a JIRA ticket for documentation and review purposes.

This skill is modeled after the existing `jira:upload-chat-log` skill but operates on Slack threads instead of the current chat conversation.

## Rationale

Our team uses Slack threads as the primary communication channel for all interactions related to a JIRA ticket. Each ticket typically has a dedicated Slack thread where:

- Team members discuss implementation details and design decisions
- Questions are asked and answered in real-time
- Blockers and dependencies are identified and resolved
- Progress updates and status changes are shared
- Code review feedback and technical discussions occur

This creates a rich context of collaboration that is often lost or disconnected from the formal JIRA ticket documentation. By uploading the Slack thread as an attachment to the corresponding JIRA ticket, we:

1. **Preserve context**: Capture the full discussion history alongside the ticket for future reference
2. **Improve traceability**: Link informal conversations to formal issue tracking
3. **Enable knowledge sharing**: Allow team members who weren't in the thread to understand the decision-making process
4. **Support auditing**: Provide a complete record of how and why decisions were made
5. **Reduce context switching**: Keep all ticket-related information in one place

### Example Thread

See: https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869

## Input

### Slack Thread Link (Required)

The skill accepts a Slack thread URL as input. The link should be provided by the user in one of these formats:

- Direct thread link: `https://workspace.slack.com/archives/C01234567/p1234567890123456`
- Thread link with reply: `https://workspace.slack.com/archives/C01234567/p1234567890123456?thread_ts=1234567890.123456`

The skill should:
1. Parse the Slack URL to extract the channel ID and thread timestamp
2. Validate the URL format before attempting to fetch
3. Provide clear error messages for invalid URLs

### JIRA Ticket Key (Optional)

- If provided by the user, use the specified ticket key
- Otherwise, search the conversation context for JIRA ticket references
- If no ticket is found, prompt the user to provide one

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `JIRA_API_TOKEN` environment variable must be set with a valid API token for https://issues.redhat.com
- `SLACK_API_TOKEN` environment variable must be set with a valid Slack Bot or User token with appropriate scopes
- Appropriate JIRA permissions to add attachments to the target ticket
- Slack token must have `channels:history`, `groups:history`, or `im:history` scopes depending on channel type

## Usage

```
/jira:upload-slack-thread <slack-thread-url> [ticket-key]
```

### Examples

```
/jira:upload-slack-thread https://redhat.slack.com/archives/C01ABC123/p1706123456789012 AIPCC-1234
```

```
/jira:upload-slack-thread https://redhat.slack.com/archives/C01ABC123/p1706123456789012
# Skill will prompt for or detect ticket from context
```

## Implementation Requirements

### Step 1: Parse and Validate Slack URL

1. Accept the Slack thread URL from user input
2. Parse the URL to extract:
   - Workspace domain
   - Channel ID
   - Thread timestamp (from `p` parameter or `thread_ts` query param)
3. Validate URL format and provide clear error for malformed URLs

### Step 2: Determine JIRA Ticket Key

1. If a ticket key is provided by the user, use it
2. Otherwise, search conversation history for JIRA ticket references
3. If no ticket found, prompt the user for the ticket key

### Step 3: Fetch Slack Thread Content

1. Use Slack API `conversations.replies` endpoint to fetch thread messages
2. Retrieve all messages in the thread including:
   - Parent message
   - All replies
   - User display names (resolve user IDs to names)
   - Timestamps
   - Message content including formatting
   - File attachments (metadata only, not actual files)
   - Reactions (optional)

### Step 4: Format as Markdown Document

Create a document with the following structure:

```markdown
# Slack Thread Export - JIRA Ticket: [ticket-key]

**Exported**: [current timestamp]
**Ticket**: https://issues.redhat.com/browse/[ticket-key]
**Slack Thread**: [original slack URL]
**Channel**: [channel name]

---

## Summary

[AI-generated summary of the thread discussion including:
- Main topic discussed
- Key decisions or conclusions
- Action items mentioned
- Participants involved
- 3-5 paragraphs maximum]

---

## Full Thread Transcript

### [User Name] - [timestamp]
[Message content]

### [User Name] - [timestamp]
[Reply content]

...
```

### Step 5: Save to Temporary File

1. Create a temporary file: `slack-thread-{ticket-key}-{timestamp}.md`
2. Write the formatted content to this file
3. Store in `/tmp/claude/` directory

### Step 6: Upload to JIRA

1. Use the existing upload script at `scripts/upload_chat_log.py` (or create a shared upload utility)
2. Run the script to upload the markdown file to the specified JIRA ticket
3. Handle success and error responses

### Step 7: Confirm and Clean Up

1. If successful, inform user with direct link to the JIRA ticket
2. If failed, display error and troubleshooting guidance
3. Delete the temporary file after upload attempt

## Script Requirements

Create a new script `scripts/fetch_slack_thread.py` that:

1. Accepts a Slack thread URL as input
2. Uses the Slack API to fetch all messages in the thread
3. Resolves user IDs to display names
4. Outputs formatted markdown to stdout or a specified file
5. Uses PEP 723 inline script metadata for dependencies:
   ```python
   #!/usr/bin/env -S uv run --script
   # /// script
   # dependencies = [
   #     "slack-sdk>=3.0.0",
   # ]
   # ///
   ```

## Error Handling

- **Missing SLACK_API_TOKEN**: Provide instructions on obtaining a Slack token with required scopes
- **Missing JIRA_API_TOKEN**: Provide instructions on obtaining a JIRA API token
- **Invalid Slack URL**: Clear message about expected URL format
- **Channel Not Found**: Check permissions and channel accessibility
- **Thread Not Found**: Verify the thread timestamp is correct
- **Permission Denied (Slack)**: Token may lack required scopes
- **Permission Denied (JIRA)**: Token may lack attachment permissions
- **Rate Limiting**: Handle Slack API rate limits gracefully

## Security Considerations

- Slack and JIRA tokens should only be read from environment variables
- Do not log or display token values
- Sanitize message content to prevent injection issues
- Consider PII in Slack messages when uploading to JIRA

## Future Enhancements

- Support for uploading file attachments from Slack thread
- Option to include or exclude reactions
- Configurable summary depth
- Support for multiple threads in one upload
- Integration with Slack MCP server when available
