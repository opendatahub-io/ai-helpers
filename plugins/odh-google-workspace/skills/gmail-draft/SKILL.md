---
name: gmail-draft
description: >-
  Use this skill to compose a Gmail draft from text content in the conversation.
  Accepts a body, recipient list, and subject — either from the user or from
  context — and creates a draft in the user's Gmail Drafts folder via gws.
argument-hint: "[subject]"
allowed-tools: Bash, AskUserQuestion
user-invocable: true
metadata:
  author: dhellman
  version: "1.0"
  tags: gmail, email, draft, google-workspace
---

# Gmail Draft

Compose a Gmail draft from text content provided in the conversation.

## Prerequisites

- `gws` binary must be on `$PATH`
- Authenticated with Gmail compose scope: run `gws auth login` (not `--readonly`)

If `gws` is not installed or authentication fails, tell the user to follow the
setup instructions in the `google-workspace` skill.

Helper scripts are located in `${CLAUDE_SKILL_DIR}` and require Python 3.10+.

---

## Step 1: Gather Recipients, Subject, and Body

Collect the three required inputs. Sources depend on how the skill was invoked:

- **From another skill** (e.g. `email-meeting-summary`): recipients, subject,
  and body are passed in context — use them directly.
- **Standalone invocation**: use `AskUserQuestion` to collect any that are
  missing:
  - Recipients: "Who should receive this email? (comma-separated addresses)"
  - Subject: "What should the subject line be?"
  - Body: "Paste or describe the content you want in the email body."

---

## Step 2: Present for Review

Show the user the draft details before creating:

```text
To: <recipients>
Subject: <subject>

<body>
```

Ask:

> "Does this look right? Reply with any edits, or say 'send' to create the
> draft."

Incorporate edits and re-present until the user approves.

---

## Step 3: Create the Draft

Write the body to a temp file, then call `create_draft.py`:

```bash
BODY_FILE=$(mktemp /tmp/gmail_draft_body.XXXXXX)
cat > "$BODY_FILE" << 'BODY_EOF'
<approved body text>
BODY_EOF

python3 "${CLAUDE_SKILL_DIR}/scripts/create_draft.py" \
  --to "<recipients>" \
  --subject "<subject>" \
  --body-file "$BODY_FILE"
```

---

## Step 4: Confirm

On success, tell the user:

> "Draft created. You can find it in the Drafts folder in Gmail at
> https://mail.google.com/mail/#drafts. Review it before sending."

If the script exits with an error, show the error message and suggest the user
check `gws auth login` permissions (the Gmail scope must include draft
creation).

---

## Error Reference

| Situation | Action |
|---|---|
| `gws` not found | Tell user to install `gws` and add it to PATH |
| Auth error (401/403) | Tell user to run `gws auth login` (without `--readonly`) |
| `create_draft.py` fails | Show error; check Gmail scope in `gws auth login` |
