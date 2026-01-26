# Quickstart: JIRA Upload Slack Thread

**Feature**: Upload Slack Thread to JIRA  
**Date**: 2026-01-26  
**Audience**: Developers and users of the skill  

## Prerequisites

### Environment Configuration

Create a `.env` file in your project root with (or point to a .env file in the system):

```bash
# .env file
JIRA_PROJECT_URL=https://jounce.atlassian.net/
JIRA_API_TOKEN=your-api-token-here
```

**OR** set environment variables:
```bash
export JIRA_PROJECT_URL="https://jounce.atlassian.net/"
export JIRA_API_TOKEN="your-api-token-here"
```


Before using this skill, ensure you have:  

1. **Python 3.13+** and **UV** installed  
   ```bash  
   python --version  # Should be 3.13 or higher  
   uv --version      # Should be installed  
   ```  

2. **Slack MCP Server** configured and running  
   - See: https://github.com/redhat-community-ai-tools/slack-mcp  
   - Must have `SLACK_XOXC_TOKEN` and `SLACK_XOXD_TOKEN` configured  

3. **JIRA MCP Server** configured and running  


4. **Permissions**:  
   - Slack: Read access to channels/threads you want to export  
   - JIRA: Comment permission on target tickets  

## Installation

based on https://github.com/opendatahub-io/ai-helpers


## Basic Usage

### Example 1: Upload with Explicit Ticket Key

```bash
./upload_slack_thread.py \
  "https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869" \
  JN-1234
```

**What happens**:  
1. ✓ Parses Slack URL and extracts channel/timestamp  
2. ✓ Fetches thread messages via Slack MCP server  
3. ✓ Formats messages as markdown  
4. ✓ Posts as comment to JIRA ticket JN-1234  
5. ✓ Displays success message with ticket link  

**Expected output**:  
```text
Found thread in #team-discussion with 12 messages
Posting to JIRA ticket JN-1234...

✓ Successfully posted Slack thread to JN-1234
  View: https://jounce.atlassian.net/browse/JN-1234
  Messages exported: 12
```

---  

### Example 2: Auto-Detect Ticket from Thread

If the Slack thread mentions a JIRA ticket (e.g., "Working on JN-1234"), you can omit the ticket key:  

```bash
./upload_slack_thread.py \
  "https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869"
```

**What happens**:  
1. ✓ Searches thread messages for JIRA ticket pattern `[A-Z]+-\d+`  
2. ✓ Finds "JN-1234" in first message  
3. ✓ Uses that ticket automatically  
4. ✓ Proceeds with export  

**If no ticket found in thread**:  
```text
No JIRA ticket found in thread. Which ticket should this be posted to?
Enter ticket key (e.g., JN-1234): _
```

---  

### Example 3: Include AI Summary

Generate a concise summary before the full transcript:  

```bash
./upload_slack_thread.py \
  "https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869" \
  JN-1234 \
  --ai-summary
```

**What happens**:  
1. ✓ Fetches thread messages  
2. ✓ Generates AI summary (1-2 paragraphs) covering main topics, decisions, participants  
3. ✓ Prepends summary to markdown export  
4. ✓ Posts to JIRA  

**Expected output includes**:  
```text
Generating AI summary...
✓ Summary generated (2 paragraphs covering main discussion points)
Posting to JIRA ticket JN-1234...
✓ Successfully posted Slack thread to JN-1234
```

**Markdown format**:  
```markdown
# Slack Thread Export - JN-1234

**Exported**: 2026-01-26T10:30:00Z
**Slack Thread**: https://redhat-internal.slack.com/archives/...
**Channel**: #team-discussion

## Summary

The team discussed implementing feature X with a focus on...
Key decisions included using approach Y because...
Action items: John to review PR, Sarah to update docs.

## Full Thread Transcript

### John Doe - 2026-01-26 10:15
Let's discuss the implementation...

[rest of messages]
```

---  

### Example 4: Verbose Mode for Debugging

Enable detailed logging to see what's happening:  

```bash
./upload_slack_thread.py \
  "https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869" \
  JN-1234 \
  --verbose
```

**Additional output** (to stderr):  
```text
[DEBUG] Parsing URL: https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869
[DEBUG] Extracted channel: C09Q8MD1V0Q, timestamp: 1769333522.823869
[DEBUG] Connecting to Slack MCP server...
[DEBUG] Fetching thread messages...
[DEBUG] Retrieved 12 messages from thread
[DEBUG] Resolving user IDs to display names...
[DEBUG] Formatting markdown (no summary)
[DEBUG] Connecting to JIRA at https://jounce.atlassian.net/
[DEBUG] Posting comment to ticket JN-1234...
[DEBUG] Comment posted successfully (ID: 12345678)
✓ Successfully posted Slack thread to JN-1234
```

## Common Use Cases

### Use Case 1: Document Sprint Planning Discussion

**Scenario**: Team had a Slack thread discussing sprint planning. Upload to sprint ticket for documentation.  

```bash
# Thread URL from Slack discussion
THREAD_URL="https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869"

# Sprint ticket
TICKET="JN-1234"

# Upload with summary for quick reference
./upload_slack_thread.py "$THREAD_URL" "$TICKET" --summary
```

**Result**: Sprint ticket now has complete discussion context with summary.  

---  

### Use Case 2: Capture Design Decisions

**Scenario**: Architecture discussion happened in Slack. Need to preserve it with design ticket.  

```bash
# Design discussion thread
THREAD_URL="https://workspace.slack.com/archives/C01ABC123/p1706123456789012"

# Design ticket mentioned in thread (auto-detected)
./upload_slack_thread.py "$THREAD_URL"
```

**Result**: Design ticket automatically linked, full discussion preserved.  

---  

### Use Case 3: Bug Investigation Thread

**Scenario**: Bug investigation with multiple team members in Slack. Upload to bug ticket.  

```bash
# Bug investigation thread (50+ messages)
THREAD_URL="https://workspace.slack.com/archives/C01ABC123/p1706123456789012"
TICKET="AIPCC-5678"

# Upload (will truncate to 50 messages with warning)
./upload_slack_thread.py "$THREAD_URL" "$TICKET" --verbose
```

**Expected output**:  
```text
Found thread in #bugs with 75 messages
⚠️ Thread exceeds 50 message limit - truncating to first 50 messages
Posting to JIRA ticket AIPCC-5678...
✓ Successfully posted Slack thread to AIPCC-5678
  Messages exported: 50 of 75 (truncated)
```

## Troubleshooting

### Error: "Unable to connect to JIRA MCP server"

**Fix**:  
1. Verify MCP server is running:  
   ```bash  
   # Check MCP server process  
   ps aux | grep jira-mcp  
   ```  

2. Check MCP configuration includes Slack server:  
   ```json  
   {  
     "mcpServers": {  
       "jira": {  
         "command": "podman",  
         "args": ["run", "-i", "--rm", ...],  
         "env": {  
            ...
         }  
       }  
     }  
   }  
   ```  

3. Restart Claude Code to reload MCP configuration  


---  

### Error: "Unable to connect to Slack MCP server"

**Fix**:  
1. Verify MCP server is running:  
   ```bash  
   # Check MCP server process  
   ps aux | grep slack-mcp  
   ```  

2. Check MCP configuration includes Slack server:  
   ```json  
   {  
     "mcpServers": {  
       "slack": {  
         "command": "podman",  
         "args": ["run", "-i", "--rm", ...],  
         "env": {  
           "SLACK_XOXC_TOKEN": "xoxc-...",  
           "SLACK_XOXD_TOKEN": "xoxd-..."  
         }  
       }  
     }  
   }  
   ```  

3. Restart Claude Code to reload MCP configuration  

---  

### Error: "Invalid Slack thread URL format"

**Fix**:  
Ensure URL is in correct format:  
```text
✓ Correct: https://workspace.slack.com/archives/C01ABC123/p1234567890123456
✗ Wrong:   https://slack.com/messages/C01ABC123
✗ Wrong:   C01ABC123/1234567890.123456
```

To get correct URL:  
1. Open Slack thread in web browser  
2. Click "Share" → "Copy link"  
3. Use that URL  

---  

### Error: "Unable to access ticket JN-1234"

**Possible causes**:  
1. **Ticket doesn't exist**: Verify at https://jounce.atlassian.net/browse/JN-1234  
2. **No permission**: Ask ticket owner to grant you access  
3. **Invalid token**: Regenerate JIRA API token  

**Fix**:  
```bash
# Test JIRA access manually
curl -u your-email@redhat.com:$JIRA_API_TOKEN \
  https://jounce.atlassian.net/rest/api/2/issue/JN-1234

# Should return ticket JSON if accessible
```

---  

### Warning: "Thread truncated: showing 50 of 150 messages"

**This is expected behavior** for threads >50 messages (per FR-009a).  

**Options**:  
1. **Accept truncation**: First 50 messages usually capture key context  
2. **Split thread**: Ask team to continue discussion in new thread  
3. **Manual export**: Use Slack export feature for full history  

**Future enhancement**: Chunking into multiple comments (currently out of scope)  

## Advanced Usage

### Pipe from Another Script

```bash
# Generate URL programmatically
THREAD_URL=$(get_latest_thread.sh)

# Upload directly
./upload_slack_thread.py "$THREAD_URL" JN-1234
```

---  

### Batch Processing

```bash
# Upload multiple threads to same ticket
for url in thread1_url thread2_url thread3_url; do
  ./upload_slack_thread.py "$url" JN-1234
done
```

---  

### Integration with CI/CD

```bash
#!/bin/bash
# In deployment script

DEPLOYMENT_THREAD="https://..."
RELEASE_TICKET="REL-123"

./upload_slack_thread.py "$DEPLOYMENT_THREAD" "$RELEASE_TICKET" --summary

echo "Deployment discussion archived to $RELEASE_TICKET"
```

## Tips & Best Practices

1. **Use `--ai-summary` for long threads**: Easier for stakeholders to get context quickly  

2. **Add ticket reference in Slack**: Mention ticket key in first message for auto-detection  
   ```text  
   "Let's discuss JN-1234 implementation"  
   ```  

3. **Export early**: Don't wait until thread is huge (>50 messages will truncate)  

4. **Combine with JIRA comments**: Add your own analysis/summary in a follow-up comment  



## Next Steps

- **Read the SKILL.md**: Full implementation details and architecture  
- **Run tests**: `pytest tests/contract/test_upload_slack_thread_contract.py`  
- **Contribute**: Check tasks.md for implementation tasks  
- **Report issues**: Create ticket with detailed error messages  

## Support

- **Documentation**: See SKILL.md in this skill directory  
- **Issues**: Report at repository issue tracker  
- **Slack MCP**: https://github.com/redhat-community-ai-tools/slack-mcp  
- **JIRA API**: https://jounce.atlassian.net/  
