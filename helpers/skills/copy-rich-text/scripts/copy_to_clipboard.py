#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["markdown", "pyobjc-framework-Cocoa; sys_platform == 'darwin'"]
# ///
"""
Copy markdown content to clipboard as rich text for pasting into Slack.

Detects whether the input contains a markdown table:
- If a table is detected, the entire output is converted to a single table
  using Google Sheets-style HTML (required for Slack table rendering).
- If no table is detected, the markdown is converted to simple HTML.

Both modes set the clipboard with proper pasteboard types so the content
pastes as formatted rich text in Slack, email, and other rich text editors.

Usage:
    echo "# Hello\n- item 1\n- item 2" | ./copy_to_clipboard.py
    echo "| A | B |\n|---|---|\n| 1 | 2 |" | ./copy_to_clipboard.py
"""

import html
import platform
import re
import subprocess
import sys


def has_markdown_table(text: str) -> bool:
    """Detect if text contains a markdown table."""
    lines = text.strip().split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", stripped):
            if i > 0 and "|" in lines[i - 1]:
                return True
    return False


def split_around_table(text: str) -> tuple[str, list[str], str]:
    """Split text into (before, table_lines, after) around the first table."""
    lines = text.strip().split("\n")
    sep_regex = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")

    # Find the separator line
    sep_idx = None
    for i, line in enumerate(lines):
        if sep_regex.match(line.strip()) and i > 0 and "|" in lines[i - 1]:
            sep_idx = i
            break

    if sep_idx is None:
        return text, [], ""

    # Walk backward from separator to find table start (header row)
    table_start = sep_idx - 1

    # Walk forward from separator to find table end
    table_end = sep_idx + 1
    while table_end < len(lines):
        stripped = lines[table_end].strip()
        if not stripped or "|" not in stripped:
            break
        table_end += 1

    before = "\n".join(lines[:table_start]).strip()
    table = [line for line in lines[table_start:table_end] if not sep_regex.match(line.strip())]
    after = "\n".join(lines[table_end:]).strip()

    return before, table, after


def table_lines_to_tsv(table_lines: list[str]) -> str:
    """Convert extracted table lines to TSV."""
    tsv_lines = []
    for line in table_lines:
        stripped = line.strip()
        cells = [c.strip() for c in stripped.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        non_empty = [c for c in cells if c]
        if len(non_empty) >= 2:
            tsv_lines.append("\t".join(cells))
    return "\n".join(tsv_lines)


def tsv_to_sheets_html(tsv: str) -> str:
    """Convert TSV text to Google Sheets-style HTML that Slack recognizes."""
    lines = tsv.strip().split("\n")
    rows_html = []
    for i, line in enumerate(lines):
        cells = line.split("\t")
        cells_html = []
        for cell in cells:
            escaped = html.escape(cell)
            style = "overflow:hidden;padding:2px 3px;vertical-align:bottom;"
            if i == 0:
                style += "font-weight:bold;"
            cells_html.append(f'<td style="{style}">{escaped}</td>')
        rows_html.append(f'<tr style="height:21px;">{"".join(cells_html)}</tr>')

    return (
        "<meta charset='utf-8'>"
        "<google-sheets-html-origin>"
        '<style type="text/css">'
        "<!--td {border: 1px solid #cccccc;}"
        "br {mso-data-placement:same-cell;}-->"
        "</style>"
        '<table xmlns="http://www.w3.org/1999/xhtml" cellspacing="0" '
        'cellpadding="0" dir="ltr" border="1" '
        'style="table-layout:fixed;font-size:10pt;font-family:Arial;'
        'width:0px;border-collapse:collapse;border:none" '
        'data-sheets-root="1" data-sheets-baot="1">'
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )


def markdown_to_html(text: str) -> str:
    """Convert markdown to HTML using the markdown library."""
    import markdown

    return markdown.markdown(text, extensions=["fenced_code", "codehilite", "tables"])


def copy_to_clipboard(text: str, html_content: str) -> None:
    """Set clipboard with both plain text and HTML, platform-aware."""
    system = platform.system()
    if system == "Darwin":
        _copy_darwin(text, html_content)
    elif system == "Linux":
        _copy_linux(text, html_content)
    else:
        print(f"Unsupported platform: {system}", file=sys.stderr)
        sys.exit(1)


def _copy_darwin(text: str, html_content: str) -> None:
    """Set clipboard on macOS with both plain text and HTML."""
    from AppKit import NSPasteboard, NSPasteboardTypeHTML, NSPasteboardTypeString

    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.declareTypes_owner_([NSPasteboardTypeString, NSPasteboardTypeHTML], None)
    pb.setString_forType_(text, NSPasteboardTypeString)
    pb.setString_forType_(html_content, NSPasteboardTypeHTML)


def _copy_linux(text: str, html_content: str) -> None:
    """Set clipboard on Linux with both plain text and HTML."""
    try:
        subprocess.run(
            ["wl-copy", "--type", "text/html"],
            input=html_content.encode(),
            check=True,
            capture_output=True,
        )
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/html"],
            input=html_content.encode(),
            check=True,
            capture_output=True,
        )
        print(
            "Warning: only HTML set (plain text fallback not available with xclip)",
            file=sys.stderr,
        )
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    try:
        subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text.encode(),
            check=True,
            capture_output=True,
        )
        print(
            "Warning: only plain text set (install xclip for HTML support)",
            file=sys.stderr,
        )
        return
    except FileNotFoundError:
        pass

    print(
        "Error: no clipboard tool found. Install xclip, xsel, or wl-clipboard.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    if sys.stdin.isatty():
        print(
            "Usage: echo '# Title\\n- item' | ./copy_to_clipboard.py",
            file=sys.stderr,
        )
        sys.exit(1)

    markdown = sys.stdin.read()
    if not markdown.strip():
        print("Error: no input", file=sys.stderr)
        sys.exit(1)

    if has_markdown_table(markdown):
        before, table_lines, after = split_around_table(markdown)
        tsv = table_lines_to_tsv(table_lines)
        html_content = tsv_to_sheets_html(tsv)
        copy_to_clipboard(tsv, html_content)
        lines = tsv.strip().split("\n")
        cols = len(lines[0].split("\t")) if lines else 0
        print(f"Copied {len(lines)}x{cols} table to clipboard")
    else:
        html_content = markdown_to_html(markdown)
        copy_to_clipboard(markdown, html_content)
        print("Copied rich text to clipboard")


if __name__ == "__main__":
    main()
