---
name: jira-workitem-attach
description: Upload file attachments to Jira tickets. Verifies file exists and uploads via Jira API. Use when user wants to attach files to tickets.
allowed-tools: Bash, Skill
user-invocable: true
---

# Jira Workitem Attach

Upload file attachments to Jira tickets using the Jira REST API (since `acli` does not support attachment uploads).

## Prerequisites

- `acli` must be installed and authenticated (`acli jira auth`) to verify the upload
- Python 3.10+ and `uv` must be installed
- `JIRA_API_TOKEN` environment variable must be set with a valid API token
- `JIRA_EMAIL` environment variable must be set with the email address associated with your Atlassian account

**Security Note**: The `JIRA_API_TOKEN` is sensitive and should be kept secure:
- Never log or echo the token value
- Avoid running debug commands that print environment variables
- The upload script handles the token securely via HTTPS
- Do not share logs or command output that may contain the token

## Implementation

### Step 1: Verify ACLi Setup

Before proceeding, verify that acli is installed and authenticated by invoking the `acli-setup-check` skill:

```text
/acli-setup-check
```

If the setup check fails, stop execution and guide the user to fix the issue.

### Step 2: Verify Environment Variables

Check that the required environment variables are set:

```bash
if [[ -z "$JIRA_API_TOKEN" || -z "$JIRA_EMAIL" ]]; then
  echo "Error: JIRA_API_TOKEN and JIRA_EMAIL environment variables must be set"
  exit 1
fi
```

If either variable is missing, inform the user:

```text
JIRA_API_TOKEN and JIRA_EMAIL environment variables are required for uploading attachments.

To set them:
  export JIRA_EMAIL="your-email@redhat.com"
  export JIRA_API_TOKEN="your-api-token"

Get your API token from:
  https://id.atlassian.com/manage-profile/security/api-tokens
```

Note: The Python upload script will also validate these variables, but checking early provides better user experience.

### Step 3: Determine Ticket Key and File Path

1. **Ticket Key**:
   - If provided by user, use it
   - Otherwise, search conversation history for ticket references matching the pattern `[A-Z]+-\d+`
   - If not found, ask: "Which ticket should I attach the file to?"

2. **File Path**:
   - If user provides a file path, validate it exists
   - If user mentions a file by name, search for it in the current directory
   - If unclear, ask: "Which file should I attach?"

3. **Validate File Path Security**:

   Before proceeding to Step 4, validate the FILE_PATH for security:

   ```bash
   # Resolve to absolute path and check it exists
   FILE_PATH="<user-provided-path>"
   REAL_PATH=$(realpath -e "$FILE_PATH" 2>/dev/null)
   if [[ $? -ne 0 ]]; then
     echo "Error: File does not exist or is not accessible: $FILE_PATH"
     exit 1
   fi

   # Check if file is readable
   if [[ ! -r "$REAL_PATH" ]]; then
     echo "Error: File is not readable: $FILE_PATH"
     exit 1
   fi

   # Reject parent-traversal patterns in original path
   if [[ "$FILE_PATH" == *".."* ]]; then
     echo "Error: Parent directory traversal (..) not allowed in file path"
     exit 1
   fi

   # Restrict to allowed directories: current working directory or /tmp
   CURRENT_DIR=$(pwd)
   if [[ "$REAL_PATH" != "$CURRENT_DIR"/* ]] && [[ "$REAL_PATH" != /tmp/* ]]; then
     echo "Error: File must be in current directory or /tmp for security"
     echo "  File location: $REAL_PATH"
     echo "  Allowed: $CURRENT_DIR/* or /tmp/*"
     exit 1
   fi

   # Check for symlinks pointing outside allowed directories
   if [[ -L "$FILE_PATH" ]]; then
     echo "Error: Symlinks not allowed for security reasons"
     exit 1
   fi
   ```

   If any validation fails, surface the error to the user and abort before calling upload_attachment.py.

### Step 4: Upload Attachment

Since `acli` does not support attachment uploads, use the upload
script located at `scripts/upload_attachment.py` relative to the
`jira-workitem-attach` skill directory.

Resolve the skill directory path and execute the script directly (not via `python` or
`bash`) to invoke `uv` via the shebang:

```bash
# Resolve skill directory path (adjust based on runtime context)
# Option 1: If skill directory is known via environment or context
SKILL_DIR="<path-to-helpers>/helpers/skills/jira-workitem-attach"

# Option 2: Compute relative to repository root if available
# SKILL_DIR="${REPO_ROOT}/helpers/skills/jira-workitem-attach"

# Option 3: Use current directory if already in skill directory
# SKILL_DIR="$(pwd)"

# Execute the upload script with resolved path
"$SKILL_DIR/scripts/upload_attachment.py" "$TICKET_KEY" "$FILE_PATH"
```

Note: The skill directory path resolution method depends on how the runtime
provides context. Use whichever approach is available (environment variables,
repository-root relative paths, or explicit path configuration).

The script will:
- Verify environment variables (JIRA_API_TOKEN, JIRA_EMAIL) are set
- Validate the file exists, is readable, and check its size
- Verify the ticket exists and is accessible
- Upload the file as an attachment to the ticket
- Display success message with attachment details
- Exit with non-zero status on failure

### Step 5: Verify Upload Success

After the upload script completes, verify the attachment was successfully added using `acli`:

```bash
acli jira workitem attachment list --key <TICKET-KEY>
```

This command will display all attachments on the ticket, including the newly uploaded file. Confirm the file appears in the list with the correct name and size.

### Step 6: Report Success

After successfully uploading and verifying the attachment, report to the user:

```text
✓ Attachment uploaded to <TICKET-KEY>
  File: <filename> (<size>)
  View: https://redhat.atlassian.net/browse/<TICKET-KEY>
```

If the attachment doesn't appear in the list, report the issue and check the upload script output for errors

## Error Handling

- **acli not found**: Delegate to `acli-setup-check` skill
- **Authentication failure**: Delegate to `acli-setup-check` skill
- **All upload errors**: The Python script handles and reports:
  - Missing environment variables (JIRA_API_TOKEN, JIRA_EMAIL)
  - File not found or not readable
  - File too large (warns if > 10MB)
  - Invalid ticket key
  - Permission denied
  - Network errors

## Limitations

- `acli` does not support uploading attachments, so this skill uses the Jira REST API directly
- Requires JIRA_API_TOKEN and JIRA_EMAIL environment variables (in addition to acli auth)
- File size limits depend on Jira instance configuration (typically 10MB)
- For very large files, consider using a file sharing service and posting a link instead

## Examples

### Attach a File

```text
User: Attach error.log to AIPCC-1234
Assistant: [Verifies file exists, uploads via API]
Attachment uploaded to AIPCC-1234
File: error.log (15.2 KB)
View: https://redhat.atlassian.net/browse/AIPCC-1234
```

### Attach Chat Log

```text
User: Attach the conversation log to AIPCC-5678
Assistant: [Exports conversation, uploads to ticket]
Attachment uploaded to AIPCC-5678
File: conversation-2024-03-20.md (42.1 KB)
View: https://redhat.atlassian.net/browse/AIPCC-5678
```

### Large File Warning

```text
User: Attach large-dataset.csv to AIPCC-910
Assistant: Warning: large-dataset.csv is 15.3 MB, which exceeds the typical 10MB Jira limit.
The upload may fail. Would you like to proceed anyway?
User: Yes
Assistant: [Attempts upload]
✗ Upload failed: Request Entity Too Large (413)

Consider compressing the file or using a file sharing service instead.
```

### List Attachments After Upload

```text
User: Attach screenshot.png to AIPCC-1234
Assistant: [Uploads file]
Attachment uploaded to AIPCC-1234
File: screenshot.png (234 KB)

Current attachments on AIPCC-1234:
- screenshot.png (234 KB) - uploaded just now
- error.log (15.2 KB) - uploaded 2024-03-19
- build.log (8.1 KB) - uploaded 2024-03-18
```
