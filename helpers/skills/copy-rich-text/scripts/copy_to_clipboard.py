#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyobjc-framework-Cocoa; sys_platform == 'darwin'"]
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


def markdown_table_to_tsv(text: str) -> str:
    """Extract markdown table(s) from text and convert to TSV."""
    lines = text.strip().split("\n")
    tsv_lines = []

    for line in lines:
        stripped = line.strip()
        if re.match(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", stripped):
            continue
        if "|" in stripped:
            cells = [c.strip() for c in stripped.split("|")]
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]
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
    """Convert markdown to simple HTML suitable for Slack rich text paste."""
    lines = text.strip().split("\n")
    result = []
    in_code_block = False
    in_list = False
    code_lines = []

    for line in lines:
        if line.strip().startswith("```"):
            if in_code_block:
                result.append(
                    "<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>"
                )
                code_lines = []
                in_code_block = False
            else:
                if in_list:
                    result.append("</ul>")
                    in_list = False
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        stripped = line.strip()

        if not stripped:
            if in_list:
                result.append("</ul>")
                in_list = False
            continue

        header_match = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if header_match:
            if in_list:
                result.append("</ul>")
                in_list = False
            level = len(header_match.group(1))
            content = inline_format(header_match.group(2))
            result.append(f"<h{level}>{content}</h{level}>")
            continue

        list_match = re.match(r"^[-*+]\s+(.*)", stripped)
        if list_match:
            if not in_list:
                result.append("<ul>")
                in_list = True
            content = inline_format(list_match.group(1))
            result.append(f"<li>{content}</li>")
            continue

        num_match = re.match(r"^\d+[.)]\s+(.*)", stripped)
        if num_match:
            if not in_list:
                result.append("<ul>")
                in_list = True
            content = inline_format(num_match.group(1))
            result.append(f"<li>{content}</li>")
            continue

        if in_list:
            result.append("</ul>")
            in_list = False
        content = inline_format(stripped)
        result.append(f"<p>{content}</p>")

    if in_list:
        result.append("</ul>")
    if in_code_block:
        result.append(
            "<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>"
        )

    return "<html><body>" + "\n".join(result) + "</body></html>"


def inline_format(text: str) -> str:
    """Apply inline markdown formatting (bold, italic, code, links)."""
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


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
    pb.setString_forType_(text, NSPasteboardTypeString)
    pb.setString_forType_(html_content, NSPasteboardTypeHTML)


def _copy_linux(text: str, html_content: str) -> None:
    """Set clipboard on Linux with both plain text and HTML."""
    try:
        proc = subprocess.run(
            ["wl-copy", "--type", "text/html"],
            input=html_content.encode(),
            capture_output=True,
        )
        subprocess.run(
            ["wl-copy", "--type", "text/plain", "--paste-once"],
            input=text.encode(),
            capture_output=True,
        )
        if proc.returncode == 0:
            return
    except FileNotFoundError:
        pass

    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/html"],
            input=html_content.encode(),
            check=True,
            capture_output=True,
        )
        return
    except FileNotFoundError:
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
        tsv = markdown_table_to_tsv(markdown)
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
