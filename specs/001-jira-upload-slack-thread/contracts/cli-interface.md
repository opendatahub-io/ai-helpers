# CLI Contract: upload_slack_thread.py

**Feature**: Upload Slack Thread to JIRA  
**Date**: 2026-01-26  
**Interface Type**: Command-Line Interface  

## Command Signature

```bash
upload_slack_thread.py <slack-thread-url> [ticket-key] [options]
```

## Arguments

### Positional Arguments

#### `slack_thread_url` (REQUIRED)

**Type**: String  
**Format**: `https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP`  
**Description**: URL of the Slack thread to export  

**Valid Examples**:  
- `https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869`  
- `https://workspace.slack.com/archives/C01ABC123/p1234567890123456?thread_ts=1234567890.123456`  

**Invalid Examples**:  
- `https://slack.com/messages` (not a thread URL)  
- `C09Q8MD1V0Q` (channel ID alone)  
- `1769333522.823869` (timestamp alone)  

**Validation**:  
- Must match regex: `https://[^/]+\.slack\.com/archives/([A-Z0-9]+)/p(\d+)`  
- Channel ID must match `[A-Z0-9]+`  
- Timestamp must be numeric  

**Error Messages**:  
- `ERROR: Invalid Slack thread URL format`  
- `Expected format: https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP`  

---  

#### `ticket_key` (OPTIONAL)

**Type**: String  
**Format**: `[A-Z]+-\d+`  
**Description**: JIRA ticket key where thread will be posted as comment  

**Valid Examples**:  
- `JN-1234`  
- `AIPCC-7354`  
- `RHEL-9876`  

**Invalid Examples**:  
- `jn-1234` (lowercase)  
- `1234` (no project prefix)  
- `JN1234` (missing hyphen)  

**Validation**:  
- Must match regex: `[A-Z]+-\d+`  
- Project prefix must be uppercase letters  
- Number must be positive integer  

**Default Behavior**:  
If not provided:  
1. Search Slack thread content for JIRA ticket key (first match)  
2. If not found, prompt user: `Which JIRA ticket should this be posted to? (e.g., JN-1234): `  

**Error Messages**:  
- `ERROR: Invalid JIRA ticket key format: {provided_key}`  
- `Expected format: PROJECT-NUMBER (e.g., JN-1234, AIPCC-7354)`  

---  

### Optional Flags

#### `-s, --summary`

**Type**: Boolean flag  
**Default**: False (disabled)  
**Description**: Enable AI-generated summary of thread content  

**Behavior**:  
- When enabled: Generate 1-2 paragraph summary before full transcript  
- When disabled: Output full transcript only  
- Summary generation failure is non-blocking (continues with transcript)  

**Example Usage**:  
```bash
upload_slack_thread.py <url> JN-1234 --summary
upload_slack_thread.py <url> -s
```

---  

#### `-v, --verbose`

**Type**: Boolean flag  
**Default**: False  
**Description**: Enable verbose output for debugging  

**Behavior**:  
- Logs detailed progress messages to stderr  
- Shows API call details (without tokens)  
- Displays message count and processing steps  

**Example Usage**:  
```bash
upload_slack_thread.py <url> JN-1234 --verbose
upload_slack_thread.py <url> -v
```

---  

#### `-h, --help`

**Type**: Boolean flag  
**Description**: Display help message and exit  

**Output**:  
```text
usage: upload_slack_thread.py [-h] [-s] [-v] slack_thread_url [ticket_key]

Upload a Slack thread as a comment to a JIRA ticket.

positional arguments:
  slack_thread_url      Slack thread URL (e.g., https://workspace.slack.com/archives/C123/p456)
  ticket_key            JIRA ticket key (e.g., JN-1234, AIPCC-7354) [optional]

options:
  -h, --help            show this help message and exit
  -s, --summary         Generate AI summary of thread content
  -v, --verbose         Enable verbose output
```

## Environment Variables

### Required

#### `JIRA_API_TOKEN`

**Type**: String (secret)  
**Description**: API token for JIRA authentication at https://jounce.atlassian.net/  

**Validation**:  
- Must be set (non-empty)  
- Not validated until JIRA API call  

**Error if Missing**:  
```text
ERROR: JIRA_API_TOKEN environment variable is not set.

To obtain a JIRA API token:
1. Go to https://jounce.atlassian.net/
2. Click your profile icon > Account Settings > Security
3. Create and copy an API token
4. Set the environment variable: export JIRA_API_TOKEN='your-token'
```

### Optional (Slack MCP Server)

Slack authentication handled by MCP server (SLACK_XOXC_TOKEN, SLACK_XOXD_TOKEN configured separately in MCP server settings).  

## Exit Codes

| Code | Meaning | When |
|------|---------|------|
| 0 | Success | Thread successfully posted to JIRA |
| 1 | General Error | Any failure (see stderr for details) |
| 2 | Invalid Arguments | URL or ticket key format invalid |
| 3 | Missing Configuration | JIRA_API_TOKEN not set or MCP server unavailable |
| 4 | API Error | Slack or JIRA API call failed |

## Output Streams

### stdout (Success Output)

**Format**: Human-readable status messages  

**Example**:  
```text
Found thread in #team-discussion with 45 messages
Extracted JIRA ticket: JN-1234
Generating markdown export...
Posting to JIRA ticket JN-1234...

✓ Successfully posted Slack thread to JN-1234
  View: https://jounce.atlassian.net/browse/JN-1234
  Messages exported: 45
```

---  

### stderr (Error Output)

**Format**: Error messages with context and troubleshooting  

**Example**:  
```text
ERROR: Unable to access JIRA ticket JN-1234: Issue does not exist

Possible reasons:
  - Ticket does not exist
  - You don't have permission to view this ticket
  - Invalid API token

Verify ticket exists: https://jounce.atlassian.net/browse/JN-1234
```

## Usage Examples

### Basic Usage (Explicit Ticket)

```bash
./upload_slack_thread.py \
  https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 \
  JN-1234
```

**Output**:  
```text
Found thread in #team-discussion with 12 messages
Posting to JIRA ticket JN-1234...
✓ Successfully posted Slack thread to JN-1234
```

---  

### Auto-Detect Ticket from Thread

```bash
./upload_slack_thread.py \
  https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869
```

**Behavior**:  
- Searches thread messages for JIRA ticket pattern  
- If found `JN-1234` in first message: uses it automatically  
- If not found: prompts user for ticket key  

---  

### With AI Summary

```bash
./upload_slack_thread.py \
  https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 \
  JN-1234 \
  --summary
```

**Output includes**:  
```text
Generating AI summary...
✓ Summary generated (2 paragraphs)
Posting to JIRA ticket JN-1234...
✓ Successfully posted Slack thread to JN-1234
```

---  

### Verbose Mode

```bash
./upload_slack_thread.py \
  https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869 \
  JN-1234 \
  --verbose
```

**Additional stderr output**:  
```text
[DEBUG] Parsing URL: https://redhat-internal.slack.com/archives/...
[DEBUG] Extracted channel: C09Q8MD1V0Q, timestamp: 1769333522.823869
[DEBUG] Fetching thread messages via MCP...
[DEBUG] Retrieved 12 messages
[DEBUG] Formatting markdown (no summary)
[DEBUG] Posting comment to JIRA...
[DEBUG] Comment posted successfully
```

## Error Scenarios

### Invalid URL Format

**Input**:  
```bash
./upload_slack_thread.py https://slack.com/invalid
```

**Output** (stderr):  
```text
ERROR: Invalid Slack thread URL format

Expected format: https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP
Example: https://workspace.slack.com/archives/C01ABC123/p1234567890123456

Exit code: 2
```

---  

### Missing JIRA Token

**Input**:  
```bash
unset JIRA_API_TOKEN
./upload_slack_thread.py <url> JN-1234
```

**Output** (stderr):  
```text
ERROR: JIRA_API_TOKEN environment variable is not set.

To obtain a JIRA API token:
1. Go to https://jounce.atlassian.net/
2. Click your profile icon > Account Settings > Security
3. Create and copy an API token
4. Set the environment variable: export JIRA_API_TOKEN='your-token'

Exit code: 3
```

---  

### Thread Truncation Warning

**Input**:  
```bash
./upload_slack_thread.py <url-with-100-messages> JN-1234
```

**Output** (stdout):  
```text
Found thread in #general with 100 messages
⚠️ Thread exceeds 50 message limit - truncating to first 50 messages
Posting to JIRA ticket JN-1234...
✓ Successfully posted Slack thread to JN-1234
  Messages exported: 50 of 100 (truncated)
```

---  

### Slack MCP Server Unavailable

**Input**:  
```bash
# MCP server not running
./upload_slack_thread.py <url> JN-1234
```

**Output** (stderr):  
```text
ERROR: Unable to connect to Slack MCP server

Possible reasons:
  - MCP server is not running
  - MCP server configuration is invalid
  - SLACK_XOXC_TOKEN or SLACK_XOXD_TOKEN not set in MCP config

Check MCP server status and configuration

Exit code: 3
```

## Contract Test Requirements

All contract tests must verify:  

1. **Argument Parsing**: Correct handling of all argument combinations  
2. **Exit Codes**: Each error scenario returns correct exit code  
3. **stdout/stderr Separation**: Success to stdout, errors to stderr  
4. **Error Messages**: Actionable guidance provided for all errors  
5. **Token Security**: JIRA_API_TOKEN never logged or displayed  
6. **Input Validation**: All invalid inputs rejected with clear messages  

## Performance Contract

| Operation | Target | Measurement |
|-----------|--------|-------------|
| URL Parsing | <50ms | Time from start to SlackThreadURL creation |
| MCP Fetch (10 msgs) | <5s | Time for Slack MCP to return messages |
| Markdown Format | <1s | Time to generate markdown from messages |
| JIRA Post | <3s | Time to post comment to JIRA |
| Total Workflow | <30s | Start to success message (per SC-001) |

## Compatibility

**Supported Platforms**:  
- macOS (Darwin)  
- Linux (Ubuntu, RHEL, Fedora)  

**Python Version**: 3.13+  

**Dependencies**:  
- UV package manager (handles jira library installation)  
- Slack MCP server (separate service)  
- JIRA API access at https://jounce.atlassian.net/  

## Updated Dependencies

### JIRA MCP Server

**Change**: Use JIRA MCP server instead of jira Python library  

**Environment Variables**:  

#### `JIRA_PROJECT_URL` (REQUIRED)

**Type**: String (URL)  
**Description**: Base URL for JIRA instance  
**Source**: .env file or environment variable  

**Valid Examples**:  
- `https://jounce.atlassian.net/`  
- `https://issues.redhat.com/`  
- `https://company.atlassian.net/`  

**Validation**:  
- Must be valid HTTPS URL  
- Must end with trailing slash  

**Error if Missing**:  
```text
ERROR: JIRA_PROJECT_URL not found in environment or .env file.

Please set JIRA_PROJECT_URL in your .env file or environment:
  export JIRA_PROJECT_URL='https://jounce.atlassian.net/'

Or create .env file with:
  JIRA_PROJECT_URL=https://jounce.atlassian.net/
  JIRA_API_TOKEN=your-api-token
```

---

### Message Formatting

**Consecutive Message Merging**: Messages from the same user that appear consecutively in the thread will be merged into a single block for better readability.  

**Example Output**:  
```markdown
### John Doe - 2026-01-26 10:15
Let me share the first point

Actually, let me add more context here

And finally, here's my conclusion

### Jane Smith - 2026-01-26 10:20
Thanks for the detailed explanation!
```

Instead of:  
```markdown
### John Doe - 2026-01-26 10:15:00
Let me share the first point

### John Doe - 2026-01-26 10:15:30
Actually, let me add more context here

### John Doe - 2026-01-26 10:16:00
And finally, here's my conclusion

### Jane Smith - 2026-01-26 10:20:00
Thanks for the detailed explanation!
```
