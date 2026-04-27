---
name: jira-workitem-comment
description: Add comments to Jira tickets using simple text or Jira markup (ADF JSON). Supports rich formatting with code blocks, lists, mentions, and links. Use when user wants to comment on a ticket.
allowed-tools: Bash, AskUserQuestion, Skill
user-invocable: true
---

# Jira Workitem Comment

Add comments to Jira tickets using the `acli` CLI with support for both simple text and rich Atlassian Document Format (ADF).

## Prerequisites

- `acli` must be installed and authenticated (`acli jira auth`)

## Implementation

### Step 1: Verify ACLi Setup

Before proceeding, verify that acli is installed and authenticated by invoking the `acli-setup-check` skill:

```
/acli-setup-check
```

If the setup check fails, stop execution and guide the user to fix the issue.

### Step 2: Determine Ticket Key and Comment Content

1. **Ticket Key**:
   - If provided by user, use it
   - Otherwise, search conversation history for ticket references matching the pattern `[A-Z]+-\d+`
   - If not found, ask: "Which ticket should I comment on?"

2. **Comment Content**:
   - If the user provides comment text, use it
   - If the user wants to document a conversation or finding, infer the content from context
   - If unclear, ask: "What would you like to say in the comment?"

3. **Comment Type**:
   - **Simple text**: Default for straightforward comments
   - **Rich format**: Use when comment includes code blocks, lists, or structured content

### Step 3a: Add Simple Text Comment (Default)

For plain text comments, write the comment text to a temporary file and use acli to create the comment:

```bash
# Validate ticket key format (PROJECT-NUMBER)
TICKET_KEY="<ticket-key-from-step-2>"
if [[ ! "$TICKET_KEY" =~ ^[A-Z]+-[0-9]+$ ]]; then
  echo "Error: Invalid ticket key format. Expected PROJECT-NUMBER (e.g., AIPCC-1234)"
  exit 1
fi

# Write comment to temp file (uses system temp directory)
TMPFILE=$(mktemp -t acli-comment-XXXX.txt)
cat > "$TMPFILE" << 'EOF'
<comment text goes here>
EOF

# Create the comment with validated ticket key
acli jira workitem comment create --key "$TICKET_KEY" --body-file "$TMPFILE"

# Clean up
rm -f "$TMPFILE"
```

### Step 3b: Add Rich ADF Comment (For Formatted Content)

For comments that need rich formatting (code blocks, lists, mentions, links), construct an ADF JSON structure.

#### ADF Structure Examples

**Basic text with formatting:**
```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "This is "},
        {"type": "text", "text": "bold text", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " and "},
        {"type": "text", "text": "italic text", "marks": [{"type": "em"}]}
      ]
    }
  ]
}
```

**Code block:**
```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Here's the fix:"}
      ]
    },
    {
      "type": "codeBlock",
      "attrs": {"language": "python"},
      "content": [
        {
          "type": "text",
          "text": "def hello():\n    print('Hello, world!')"
        }
      ]
    }
  ]
}
```

**Bullet list:**
```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [
            {
              "type": "paragraph",
              "content": [{"type": "text", "text": "First item"}]
            }
          ]
        },
        {
          "type": "listItem",
          "content": [
            {
              "type": "paragraph",
              "content": [{"type": "text", "text": "Second item"}]
            }
          ]
        }
      ]
    }
  ]
}
```

**Link:**
```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "See "},
        {
          "type": "text",
          "text": "the documentation",
          "marks": [
            {
              "type": "link",
              "attrs": {"href": "https://example.com/docs"}
            }
          ]
        }
      ]
    }
  ]
}
```

**User mention:**
```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "mention",
          "attrs": {
            "id": "557058:12345678-abcd-1234-abcd-123456789012",
            "text": "@code-samurai"
          }
        },
        {"type": "text", "text": " please review"}
      ]
    }
  ]
}
```

Write the ADF JSON to a temporary file and create the comment:

```bash
# Validate ticket key format (PROJECT-NUMBER)
TICKET_KEY="<ticket-key-from-step-2>"
if [[ ! "$TICKET_KEY" =~ ^[A-Z]+-[0-9]+$ ]]; then
  echo "Error: Invalid ticket key format. Expected PROJECT-NUMBER (e.g., AIPCC-1234)"
  exit 1
fi

# Write ADF JSON to temp file (uses system temp directory)
TMPFILE=$(mktemp -t acli-comment-XXXX.json)
cat > "$TMPFILE" << 'EOF'
{
  "version": 1,
  "type": "doc",
  "content": [...]
}
EOF

# Create comment with ADF and validated ticket key
acli jira workitem comment create --key "$TICKET_KEY" --body-file "$TMPFILE"

# Clean up
rm -f "$TMPFILE"
```

### Step 4: Confirm Comment Content (Optional)

For important or lengthy comments, show a preview to the user:

```
I'll add this comment to <TICKET-KEY>:

---
<comment preview>
---

Should I proceed?
```

Wait for confirmation before creating the comment.

### Step 5: Report Success

After successfully creating the comment, report to the user:

```
Comment added to <TICKET-KEY>
View: https://redhat.atlassian.net/browse/<TICKET-KEY>
```

## When to Use Rich Formatting

Use ADF (Step 3b) when the comment includes:

1. **Code snippets or blocks**: Error messages, logs, code examples
2. **Structured lists**: Action items, requirements, test cases
3. **Links**: References to PRs, documentation, external resources
4. **Mentions**: Tagging specific users for attention
5. **Mixed formatting**: Bold headers, italic emphasis, inline code

Use simple text (Step 3a) for:

1. Brief updates or status notes
2. Simple questions or answers
3. Acknowledgments or confirmations

## Error Handling

- **acli not found**: Delegate to `acli-setup-check` skill
- **Authentication failure**: Delegate to `acli-setup-check` skill
- **Invalid ticket key**: Verify format and ticket existence
- **Permission denied**: Check user has permission to comment on the ticket
- **Invalid ADF**: Verify JSON structure matches ADF schema
- **Comment too long**: Jira has a 32,767 character limit per comment; suggest breaking into multiple comments

## Examples

### Simple Text Comment

```text
User: Add a comment to AIPCC-1234 saying the fix is ready for review
Assistant: [Creates simple text comment]
Comment added to AIPCC-1234
View: https://redhat.atlassian.net/browse/AIPCC-1234
```

### Code Block Comment

```text
User: Comment on AIPCC-5678 with this error message: [paste error]
Assistant: [Creates ADF comment with code block]
Comment added to AIPCC-5678 with formatted code block
View: https://redhat.atlassian.net/browse/AIPCC-5678
```

### Structured Update

```text
User: Add a status update to AIPCC-910 with these action items:
- Fix merged to main
- QA testing in progress
- Deployment scheduled for Friday
Assistant: [Creates ADF comment with bullet list]
Comment added to AIPCC-910
View: https://redhat.atlassian.net/browse/AIPCC-910
```
