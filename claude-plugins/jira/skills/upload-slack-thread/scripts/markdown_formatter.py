# Edited by Claude Code
"""
Markdown formatting for Slack thread export.

This module handles formatting Slack thread messages as markdown
for upload to JIRA. Inspired by vllm-slack-summary formatting patterns.
"""

import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from slack_fetcher import SlackThread, ThreadMessage


@dataclass
class MarkdownExport:
    """
    Represents the formatted markdown document ready for JIRA upload.

    Attributes:
        ticket_key: Target JIRA ticket (e.g., "JN-1234")
        thread_url: Original Slack thread URL
        channel_name: Slack channel name
        export_timestamp: ISO 8601 timestamp of export
        summary: AI-generated summary (if enabled)
        transcript: Formatted message transcript
        is_truncated: Whether thread was truncated
        total_message_count: Total messages in thread
        included_message_count: Messages included in export
    """
    ticket_key: str
    thread_url: str
    channel_name: str
    export_timestamp: str
    summary: str | None
    transcript: str
    is_truncated: bool
    total_message_count: int
    included_message_count: int

    @property
    def full_content(self) -> str:
        """Generate complete markdown content for JIRA comment."""
        header = f"""# Slack Thread Export - {self.ticket_key}

**Exported**: {self.export_timestamp}
**Slack Thread**: {self.thread_url}
**Channel**: #{self.channel_name}
**Messages**: {self.included_message_count}"""

        if self.is_truncated:
            header += f" *(truncated from {self.total_message_count})*"

        header += "\n"

        if self.is_truncated:
            header += f"\n⚠️ **Thread truncated**: Showing {self.included_message_count} of {self.total_message_count} messages\n"

        content = header + "\n---\n\n"

        if self.summary:
            content += f"## Summary\n\n{self.summary}\n\n"

        content += f"## Full Thread Transcript\n\n{self.transcript}"
        content += "\n---\n\n*End of transcript*"

        return content


def format_slack_text(
    text: str,
    user_lookup: dict[str, str] | None = None
) -> str:
    """
    Format Slack message text to clean markdown.

    Handles:
    - User mentions <@U123456> -> **@username**
    - Channel mentions <#C123456|channel-name> -> **#channel-name**
    - URLs <https://url|text> or <https://url> -> url
    - Code blocks (preserved)
    - Slack bold *text* -> **text**
    - Slack italic _text_ -> *text*
    - Slack strikethrough ~text~ -> ~~text~~

    Args:
        text: Raw Slack message text
        user_lookup: Optional dict mapping user_id -> display_name

    Returns:
        Formatted markdown text
    """
    if not text:
        return ""

    user_lookup = user_lookup or {}

    # Ensure code blocks have newlines around them
    text = re.sub(r"(?<!\n)(```)", r"\n\1", text)
    text = re.sub(r"(```[^`]*```)(?!\n)", r"\1\n", text)

    # Replace user mentions <@U123456> with **@username**
    def replace_mention(match: re.Match[str]) -> str:
        user_id = match.group(1)
        user_name = user_lookup.get(user_id, user_id)
        return f"**@{user_name}**"

    text = re.sub(r"<@([A-Z0-9]+)>", replace_mention, text)

    # Replace channel mentions <#C123456|channel-name> with **#channel-name**
    text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"**#\1**", text)

    # Clean up URLs - keep them but remove the < > wrapper
    text = re.sub(r"<(https?://[^|>]+)(?:\|[^>]+)?>", r"\1", text)

    # Convert Slack's bold *text* to markdown **text**
    text = re.sub(r"(?<!\*)\*(?!\*)([^\*]+)\*(?!\*)", r"**\1**", text)

    # Convert Slack's italic _text_ to markdown *text*
    text = re.sub(r"(?<!_)_(?!_)([^_]+)_(?!_)", r"*\1*", text)

    # Convert Slack's strikethrough ~text~ to markdown ~~text~~
    text = re.sub(r"~([^~]+)~", r"~~\1~~", text)

    return text


def format_attachments(attachments: list[Any] | None) -> str:
    """Format Slack attachments as markdown notes."""
    if not attachments:
        return ""

    lines = []
    for att in attachments:
        filename = getattr(att, 'filename', None) or 'unnamed'
        filetype = getattr(att, 'filetype', None) or 'file'
        lines.append(f"📄 *File:* `{filename}` ({filetype})")

    return "\n".join(lines)


def merge_consecutive_messages(messages: list[ThreadMessage]) -> list[ThreadMessage]:
    """
    Merge consecutive messages from the same user.

    This function creates new ThreadMessage objects rather than modifying the originals,
    preventing unintended side effects if the original message list is reused.

    Args:
        messages: List of thread messages in chronological order

    Returns:
        List with consecutive same-user messages merged (new objects)
    """
    if not messages:
        return []

    # Create a copy of the first message to avoid mutation
    merged = [replace(messages[0])]
    for msg in messages[1:]:
        if msg.user_id == merged[-1].user_id:
            # Create a new message with merged text instead of mutating
            merged[-1] = replace(merged[-1], text=merged[-1].text + f"\n\n{msg.text}")
        else:
            merged.append(replace(msg))

    return merged


def format_timestamp(ts: str) -> str:
    """Convert Slack timestamp to human-readable format."""
    ts_parts = ts.split('.')
    dt = datetime.fromtimestamp(int(ts_parts[0]), tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_thread_to_markdown(
    thread: SlackThread,
    ticket_key: str,
    thread_url: str,
    user_lookup: dict[str, str] | None = None
) -> MarkdownExport:
    """
    Format Slack thread as markdown for JIRA export.

    Args:
        thread: SlackThread object with messages
        ticket_key: Target JIRA ticket key
        thread_url: Original Slack thread URL
        user_lookup: Optional dict mapping user_id -> display_name

    Returns:
        MarkdownExport object ready for upload
    """
    user_lookup = user_lookup or {}

    # Merge consecutive messages from same user
    merged_messages = merge_consecutive_messages(thread.messages)

    # Format each message
    transcript_lines = []
    for msg in merged_messages:
        formatted_ts = format_timestamp(msg.timestamp)
        user_display = user_lookup.get(msg.user_id, msg.user_name)

        # Format message text with Slack formatting conversion
        formatted_text = format_slack_text(msg.text, user_lookup)

        # Format message block
        transcript_lines.append(f"**[{formatted_ts}] {user_display}:**")
        transcript_lines.append(formatted_text)

        # Add attachment notes
        if msg.attachments:
            attachment_text = format_attachments(msg.attachments)
            if attachment_text:
                transcript_lines.append(attachment_text)

        transcript_lines.append("")  # Blank line between messages

    transcript = "\n".join(transcript_lines)

    return MarkdownExport(
        ticket_key=ticket_key,
        thread_url=thread_url,
        channel_name=thread.channel_name or thread.channel_id,
        export_timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        summary=None,  # Summary generation handled by Claude
        transcript=transcript,
        is_truncated=thread.is_truncated,
        total_message_count=thread.total_message_count,
        included_message_count=len(thread.messages)
    )
