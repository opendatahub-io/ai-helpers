---
name: copy-rich-text
description: Copy the most recent assistant output to clipboard as rich text for pasting into Slack, email, or other rich text editors
allowed-tools: Bash
user-invocable: true
---

# Copy Rich Text

Copy the most recent assistant output (or user-specified content) to the clipboard as rich text suitable for pasting into Slack, email, or other rich text editors.

## Prerequisites

- **uv**: Required for running the script (`brew install uv` or `pip install uv`)
- **macOS**: No extra dependencies (uses PyObjC via uv)
- **Linux**: `xclip` (X11) or `wl-clipboard` (Wayland)
  - Fedora/RHEL: `sudo dnf install xclip`
  - Ubuntu/Debian: `sudo apt install xclip`

## How to Use

1. Identify the content to copy — use the most recent assistant output unless the user specifies something else.
2. Detect whether the content contains a Markdown table.
3. Write the Markdown content to a temporary file and pipe it to the script:

```bash
cat /tmp/rich_text_content.md | ./scripts/copy_to_clipboard.py
```

### Table detection

- **If a table is detected**: The entire output is converted to a single table. The script uses Google Sheets-style HTML with both `text/plain` (TSV) and `text/html` pasteboard types set simultaneously — this is the only format Slack recognizes for table rendering.
- **If no table is detected**: The Markdown is converted to simple HTML (headers, bold, italic, lists, code blocks, links) and set as rich text on the clipboard.

### Important

- Write the full Markdown content to a temp file first, then pipe it. Do not try to pass it inline via echo — content with special characters will break.
- When the output contains a table, the **entire** clipboard content should be the table. Strip any non-table prose and consolidate into a single table if needed.
- The first row of a table is automatically bolded as a header.

## How It Works

Slack requires specific clipboard metadata to render pasted content as a table. Regular `pbcopy` or the `hexdump | osascript` approach only sets plain text, which Slack renders as unformatted text.

This script sets **both** clipboard types simultaneously:
- `public.utf8-plain-text` — plain text (TSV for tables, markdown for prose)
- `public.html` — HTML (`<google-sheets-html-origin>` for tables, standard HTML for prose)

On macOS this uses `NSPasteboard` via PyObjC. On Linux it uses `wl-copy` (Wayland) or `xclip` (X11).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Pastes as plain text in Slack | Verify both clipboard types are set: `osascript -e 'clipboard info'` should show both `utf8` and `HTML` |
| `xclip` not found on Linux | `sudo dnf install xclip` or `sudo apt install xclip` |
| `uv` not found | `brew install uv` or `pip install uv` |
| Table renders wrong | Ensure input has proper Markdown table syntax with `\|` delimiters and `\|---\|` separator row |
| Script fails on first run | uv downloads PyObjC on first invocation — requires internet |
