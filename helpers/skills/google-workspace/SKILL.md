---
name: google-workspace
description: >
  Fetch and query data from Google Workspace using the gws CLI — Gmail, Calendar,
  Docs, Sheets, Slides, and Drive. Use this skill whenever the user mentions
  email, inbox, messages, calendar, meetings, schedule, agenda, Google Docs,
  spreadsheets, presentations, or Drive files. Trigger on phrases like "check my
  email", "what meetings do I have", "read this doc", "open this spreadsheet",
  "find files in Drive", or any Google URL (docs.google.com, drive.google.com).
allowed-tools: Bash
---

# Google Workspace

Access Google Workspace data via the `gws` CLI. Fetches content
and presents it as markdown context inside the current session.

## Prerequisites

- `gws` binary must be on `$PATH`
- Authenticated: run `gws auth login` if not already logged in

If `gws` is not installed, not on PATH, or authentication fails with a 401/403,
read `references/setup.md` for the full first-time setup walkthrough.

## Command Patterns

`gws` has two ways to call any service:

1. **Shortcut commands** (prefixed with `+`) — concise, opinionated, cover common
   tasks. Prefer these when they fit.
2. **Raw API calls** — full access to any Google API method via
   `gws <service> <resource> <method> --params '<JSON>'`. Use when shortcuts
   don't expose the parameter you need.

Try the shortcut first. Fall back to the raw API when you need filters, field
selection, pagination control, or parameters the shortcut doesn't expose.

## Extracting IDs from Google URLs

Many requests include a Google URL. Extract the document ID before calling `gws`:

| Service | URL pattern | ID location |
|---------|------------|-------------|
| Docs | `docs.google.com/document/d/<ID>/...` | between `/d/` and next `/` |
| Sheets | `docs.google.com/spreadsheets/d/<ID>/...` | between `/d/` and next `/` |
| Slides | `docs.google.com/presentation/d/<ID>/...` | between `/d/` and next `/` |
| Drive file | `drive.google.com/file/d/<ID>/...` | between `/d/` and next `/` |
| Drive folder | `drive.google.com/drive/folders/<ID>` | after `/folders/` |

Extract the ID with `sed` (works on both macOS and Linux):

```bash
URL="https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit"
DOC_ID=$(echo "$URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
```

## Shell Tips

- **zsh `!` expansion**: Sheet ranges like `Sheet1!A1` trigger history expansion
  in zsh. Use double quotes: `--range "Sheet1!A1:D10"`
- **JSON flags**: Wrap `--params` and `--json` in single quotes so the shell
  preserves inner double quotes: `--params '{"pageSize": 5}'`

## Gmail

### Triage unread messages

```bash
gws gmail +triage
gws gmail +triage --max 10
gws gmail +triage --labels
```

### List messages matching a query

Gmail search syntax works with `--query`. Common patterns:

```bash
# Messages in a label
gws gmail +triage --query 'label:my-label' --max 5

# Messages from a sender
gws gmail +triage --query 'from:alice@example.com' --max 10

# Unread messages in a label
gws gmail +triage --query 'label:updates is:unread'

# Recent messages with a subject keyword
gws gmail +triage --query 'subject:quarterly-report newer_than:7d'
```

### Read a specific message

`+triage` output includes message IDs. Use the ID to fetch the full body:

```bash
gws gmail +read --id <MESSAGE_ID>
gws gmail +read --id <MESSAGE_ID> --headers
```

### Typical workflow: "show me the latest email in label X"

```bash
# Step 1: find the message
gws gmail +triage --query 'label:X' --max 1 --format json

# Step 2: extract the ID from the JSON output, then read it
gws gmail +read --id <ID> --headers
```

### Search with the raw API

For queries that need parameters beyond what `+triage` exposes:

```bash
gws gmail users messages list --params '{"q": "has:attachment larger:5M", "maxResults": 5}'
```

## Calendar

### View upcoming events

```bash
gws calendar +agenda                          # next few upcoming events
gws calendar +agenda --today                  # today only
gws calendar +agenda --tomorrow               # tomorrow only
gws calendar +agenda --week                   # this week
gws calendar +agenda --days 3                 # next 3 days
gws calendar +agenda --calendar 'Work'        # specific calendar
gws calendar +agenda --today --format table   # table output
```

Time-aware commands like `+agenda` automatically use your Google account
timezone. Override with `--timezone America/New_York`.

### List events via the API (custom time range or filters)

```bash
# Events in the next 7 days on a specific calendar
gws calendar events list \
  --params '{"calendarId": "primary", "timeMin": "2026-04-24T00:00:00Z", "timeMax": "2026-05-01T00:00:00Z", "singleEvents": true, "orderBy": "startTime"}'
```

### Typical workflow: "show my last N calendar entries titled X"

```bash
# Use +agenda with a calendar filter, then grep or parse for matching titles
gws calendar +agenda --days 30 --calendar 'Work' --format json
```

Filter the JSON output for events matching the requested title.

## Google Docs

### Read a document

```bash
# By document ID (extracted from URL)
gws docs documents get --params '{"documentId": "<DOC_ID>"}'
```

The response is the full document JSON (structure, text runs, styles). To
extract plain text for context, pipe through `jq`:

```bash
gws docs documents get --params '{"documentId": "<DOC_ID>"}' \
  | jq -r '[.. | .textRun? // empty | .content] | join("")'
```

### Typical workflow: "read this Google Doc" (user provides URL)

```bash
DOC_ID=$(echo "$URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
gws docs documents get --params "{\"documentId\": \"$DOC_ID\"}" \
  | jq -r '[.. | .textRun? // empty | .content] | join("")'
```

## Google Sheets

### Read cell values

```bash
gws sheets +read --spreadsheet <SPREADSHEET_ID> --range "Sheet1!A1:D10"
gws sheets +read --spreadsheet <SPREADSHEET_ID> --range Sheet1
```

### Read via the API (for advanced options)

```bash
gws sheets spreadsheets values get \
  --params '{"spreadsheetId": "<ID>", "range": "Sheet1!A1:Z100"}'
```

### Resolving a sheet tab from a URL with `gid=`

Users often share URLs like `...edit?gid=1937078361`. The gid is a numeric tab
ID, not a tab name. Resolve it before reading:

```bash
SHEET_ID=$(echo "$URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
GID=$(echo "$URL" | sed -E 's|.*gid=([0-9]+).*|\1|')

# Get all tab names and their IDs
gws sheets spreadsheets get \
  --params "{\"spreadsheetId\": \"$SHEET_ID\", \"fields\": \"sheets.properties\"}" \
  | jq -r ".sheets[] | select(.properties.sheetId == $GID) | .properties.title"
```

Then use the resolved tab name in the `+read` command.

### Typical workflow: "read this spreadsheet" (user provides URL)

```bash
SHEET_ID=$(echo "$URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
# If the URL has a gid= parameter, resolve the tab name first (see above)
gws sheets +read --spreadsheet "$SHEET_ID" --range Sheet1
```

## Google Slides

### Read a presentation

```bash
gws slides presentations get --params '{"presentationId": "<PRES_ID>"}'
```

Extract text from all slides. The Slides API stores text inside
`pageElements[].shape.textContent.textElements[].textRun.content`:

```bash
gws slides presentations get --params '{"presentationId": "<PRES_ID>"}' \
  | jq -r '.slides[] | [.pageElements[]? | .shape?.textContent?.textElements[]? | .textRun?.content? // empty] | join("")'
```

### Typical workflow: "read this presentation" (user provides URL)

```bash
PRES_ID=$(echo "$URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
gws slides presentations get --params "{\"presentationId\": \"$PRES_ID\"}" \
  | jq -r '.slides[] | [.pageElements[]? | .shape?.textContent?.textElements[]? | .textRun?.content? // empty] | join("")'
```

## Google Drive

### List recent files

```bash
# 5 most recently created files
gws drive files list \
  --params '{"pageSize": 5, "orderBy": "createdTime desc", "fields": "files(id,name,mimeType,createdTime,webViewLink)"}'

# 5 most recently modified files
gws drive files list \
  --params '{"pageSize": 5, "orderBy": "modifiedTime desc", "fields": "files(id,name,mimeType,modifiedTime,webViewLink)"}'
```

### Search for files

```bash
# Files by name
gws drive files list \
  --params '{"q": "name contains '\''report'\''", "pageSize": 10, "fields": "files(id,name,mimeType,webViewLink)"}'

# Files in a specific folder
gws drive files list \
  --params '{"q": "'\''<FOLDER_ID>'\'' in parents", "pageSize": 10, "fields": "files(id,name,mimeType,webViewLink)"}'

# Only Google Docs
gws drive files list \
  --params '{"q": "mimeType='\''application/vnd.google-apps.document'\''", "pageSize": 5, "fields": "files(id,name,webViewLink)"}'

# Exclude trashed files (recommended default)
gws drive files list \
  --params '{"q": "trashed=false", "pageSize": 10, "orderBy": "modifiedTime desc", "fields": "files(id,name,mimeType,modifiedTime,webViewLink)"}'
```

### Get file metadata

```bash
gws drive files get \
  --params '{"fileId": "<FILE_ID>", "fields": "id,name,mimeType,size,createdTime,modifiedTime,webViewLink,owners"}'
```

### Export a Google Workspace file as plain text or PDF

```bash
# Export a Doc as plain text
gws drive files export \
  --params '{"fileId": "<FILE_ID>", "mimeType": "text/plain"}' \
  -o output.txt

# Export a Sheet as CSV
gws drive files export \
  --params '{"fileId": "<FILE_ID>", "mimeType": "text/csv"}' \
  -o output.csv

# Export Slides as PDF
gws drive files export \
  --params '{"fileId": "<FILE_ID>", "mimeType": "application/pdf"}' \
  -o output.pdf
```

### List files in a folder (from URL)

```bash
FOLDER_ID=$(echo "$URL" | sed -E 's|.*folders/([A-Za-z0-9_-]+).*|\1|')
gws drive files list \
  --params "{\"q\": \"'$FOLDER_ID' in parents and trashed=false\", \"pageSize\": 20, \"fields\": \"files(id,name,mimeType,modifiedTime,webViewLink)\"}"
```

## Cross-Service Workflows

Users often ask questions that span multiple services. Chain commands together:

### "Find the spreadsheet linked in my last email from Alice"

```bash
# 1. Find the email
gws gmail +triage --query 'from:alice@example.com' --max 1 --format json
# 2. Read it and look for a Google Sheets URL in the body
gws gmail +read --id <MESSAGE_ID>
# 3. Extract the spreadsheet ID from the URL and read it
SHEET_ID=$(echo "$SHEET_URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
gws sheets +read --spreadsheet "$SHEET_ID" --range Sheet1
```

### "Prep me for my next meeting"

```bash
# 1. Get the next event
gws calendar +agenda --days 1 --format json
# 2. If the event description has a Google Doc link, read it
DOC_ID=$(echo "$DOC_URL" | sed -E 's|.*/d/([A-Za-z0-9_-]+).*|\1|')
gws docs documents get --params "{\"documentId\": \"$DOC_ID\"}" \
  | jq -r '[.. | .textRun? // empty | .content] | join("")'
```

### Built-in workflow shortcuts

`gws` has built-in workflow commands for common multi-service tasks:

```bash
gws workflow +standup-report    # today's meetings + open tasks
gws workflow +meeting-prep      # next meeting: agenda, attendees, docs
gws workflow +weekly-digest     # weekly summary: meetings + unread count
```

## Presenting Results

After fetching data, present it as clean markdown:
- **Email**: show From, Subject, Date as headers, body as quoted text
- **Calendar**: show a table with Time, Title, Location columns
- **Docs/Slides**: show extracted text content, noting any formatting lost
- **Sheets**: show data as a markdown table
- **Drive**: show a table with Name, Type, Modified, Link columns

Always tell the user what was fetched and from where, so they can verify the
source.

## Error Handling

- **Not authenticated**: tell the user to run `gws auth login`
- **Permission denied**: the user may not have access to the resource
- **Invalid ID**: double-check the URL parsing extracted the correct ID
- **Empty results**: report that no results matched the query
- **gws not found**: tell the user to install gws and ensure it is on PATH

## Discovering More Commands

```bash
gws --help                                    # top-level help
gws <service> --help                          # browse resources
gws schema <service>.<resource>.<method>      # inspect method parameters
```
