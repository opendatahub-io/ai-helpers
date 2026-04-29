---
name: email-meeting-summary
description: >-
  Review a Google Meet transcript for a specific meeting topic, then compose a
  Gmail draft summarizing decisions and action items for that topic. Prompts for
  meeting selection if not specified, and for topic selection before drafting.
  Stops gracefully if the transcript is not yet available.
argument-hint: "[meeting name] [YYYY-MM-DD]"
allowed-tools: Bash, AskUserQuestion
user-invocable: true
metadata:
  author: dhellman
  version: "1.0"
  tags: meetings, google-workspace, gmail, calendar, transcript, summary
---

# Email Meeting Summary

Read a Google Meet transcript, identify discussion topics, summarize decisions
and action items for the chosen topic, and compose a Gmail draft for review.

## Prerequisites

- `gws` binary must be on `$PATH`
- Authenticated: run `gws auth login` if not already logged in. The `--readonly` flag is sufficient for reading calendar/docs/drive, but draft creation requires the `gmail.compose` scope which is included in the default (non-readonly) login.

If `gws` is not installed or authentication fails, tell the user to follow the
setup instructions in the `google-workspace` skill.

Helper scripts are located in `${CLAUDE_SKILL_DIR}` and require Python 3.10+.

---

## Step 1: Identify the Meeting

Run the search once and save the result to a temp file:

```bash
EVENT_FILE=$(mktemp /tmp/meeting_event.XXXXXX)

# With a keyword (argument provided):
python3 "${CLAUDE_SKILL_DIR}/scripts/find_meeting.py" --days 7 "<keyword>" > "$EVENT_FILE"

# With keyword + specific date (recurring meeting):
python3 "${CLAUDE_SKILL_DIR}/scripts/find_meeting.py" --days 7 --date "<YYYY-MM-DD>" "<keyword>" > "$EVENT_FILE"

# No argument — list all recent events:
python3 "${CLAUDE_SKILL_DIR}/scripts/find_meeting.py" --days 7 > "$EVENT_FILE"
```

The script always outputs JSON. Read `EVENT_FILE` and display the result(s) to
the user as a human-readable list.

The script searches the past 7 days (up to now). When a keyword matches
multiple occurrences of a recurring meeting, it automatically picks the best
one: the occurrence on `--date` if given, otherwise today's, otherwise the most
recent past one.

**Always confirm with the user** before proceeding, regardless of how many
results were found. Use `AskUserQuestion`:

> "I found: **<title>** on <date> at <time>. Is this the meeting you want to
> summarize? (yes / no — if no, describe the meeting you meant)"

If the user says no, ask for clarification and re-run `find_meeting.py` with a
corrected keyword or `--date`, overwriting `EVENT_FILE`. If multiple events were
returned, list them and ask the user to pick one by number, then re-run with
`--date` to narrow to that occurrence.

---

## Step 2: Find the Transcript in Google Drive

Pass the event JSON to `find_transcript.py` on stdin:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/find_transcript.py" < "$EVENT_FILE"
```

The script returns JSON with a `source` field:

| `source` | Meaning | What to use |
|---|---|---|
| `"attachment"` | Found in event attachments | `fileId` field |
| `"drive"` | Found via Drive search | pick from `files` array |
| `"none"` | Not found anywhere | stop gracefully |

**If `source` is `"none"`**: tell the user the transcript is not yet available
(Gemini may take several minutes after the meeting ends) and stop.

**If `source` is `"drive"` and `files` has more than one entry**: present a
numbered list (name, created date, link) and use `AskUserQuestion` to ask which
file to use.

**If exactly one result**: proceed automatically.

Store the chosen document ID as `DOC_ID`.

---

## Step 3: Read the Transcript

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/read_doc.py" "<DOC_ID>"
```

The script outputs the document as plain text. Store this as `TRANSCRIPT`. If
the script exits with an error or the output is empty, inform the user and stop.

---

## Step 4: Identify Topics and Let the User Choose

Analyze `TRANSCRIPT` to identify 3–8 distinct discussion topics or agenda
items. For each topic, write a one-sentence description of what was discussed.

Present the topics as a numbered list, for example:

```text
1. Sprint planning — The team aligned on story point allocations for the
   upcoming two-week sprint.
2. CI pipeline failures — Discussed root cause of the nightly test failures
   and assigned investigation owners.
3. Q3 roadmap review — Reviewed progress against Q3 milestones and flagged
   three items at risk.
```

Use `AskUserQuestion`:

> "Which topic would you like to summarize for the team email? Enter the number."

---

## Step 5: Generate the Summary and Present for Review

For the selected topic, extract from `TRANSCRIPT`:

**Key decisions** — concrete choices or conclusions reached (bullet list).
**Action items** — tasks assigned, including owner name and due date where
mentioned (bullet list; format each as `[Owner] Task description — due DATE`
when dates are present).

Present the formatted summary inline:

```text
## Summary: <TOPIC NAME>

### Key Decisions
- ...

### Action Items
- [Alice] Investigate nightly test failures in module X — due Friday
- [Bob] Update the roadmap slide deck before next week's review
```

Ask the user:

> "Does this summary look correct? Reply with any edits, or say 'approved' to
> draft the email."

Incorporate any requested edits and re-present until the user approves.

---

## Step 6: Compose a Gmail Draft

Write the approved summary body to a temp file, then call `create_draft.py`:

```bash
# Write the body to a dynamically named temp file
BODY_FILE=$(mktemp /tmp/meeting_summary_body.XXXXXX)
cat > "$BODY_FILE" << 'BODY_EOF'
<approved summary text>
BODY_EOF

# Create the draft
TO="<comma-separated attendee emails from Step 1>"
SUBJECT="[Meeting Summary] $EVENT_TITLE — <selected topic name>"

python3 "${CLAUDE_SKILL_DIR}/scripts/create_draft.py" \
  --to "$TO" \
  --subject "$SUBJECT" \
  --body-file "$BODY_FILE"
```

On success, confirm to the user:

> "Draft created. You can find it in the Drafts folder in Gmail at
> https://mail.google.com/mail/#drafts. Review it before sending."

If the script exits with an error, show the error message and suggest the user
check `gws auth login` permissions (the Gmail scope must include draft creation).

---

## Error Reference

| Situation | Action |
|---|---|
| `gws` not found | Tell user to install `gws` and add it to PATH |
| Auth error (401/403) | Tell user to run `gws auth login` |
| No calendar events found | Widen search with `--days N` or ask user for the exact date |
| `find_transcript.py` returns `"none"` | Inform user; transcript may not be ready yet |
| `read_doc.py` returns empty output | Inform user; doc may be empty or wrong file |
| `create_draft.py` fails | Show error; check Gmail scope in `gws auth login` |
