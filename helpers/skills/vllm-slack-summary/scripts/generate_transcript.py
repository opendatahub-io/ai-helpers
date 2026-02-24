#!/usr/bin/env python3
"""
Generate Slack Transcript for vLLM Slack Summary

Exports Slack channel messages and converts them to a markdown transcript
for Claude to summarize.

Prerequisites:
    - slackdump: CLI tool for exporting Slack messages (https://github.com/rusq/slackdump)

What this script does:
    1. Exports messages from a Slack channel for the specified time period using slackdump
    2. Converts the JSON export to a readable markdown transcript
    3. Outputs the transcript with a summary prompt for Claude to process

Usage:
    python generate_transcript.py [--days N] [--channel CHANNEL_ID] [--output-dir DIR]

Arguments:
    --days        Number of days to look back (default: 7)
    --channel     Slack channel ID (default: C07R5PAL2L9 for vLLM CI SIG)
    --output-dir  Directory for output files (default: vllm_slack_summary)

Output:
    Creates a directory containing:
    - slack_export/: Raw slackdump export data
    - transcript.md: Formatted markdown transcript of conversations
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from typing import Any, Dict, List

# Security validation patterns
# Slack channel IDs: alphanumeric, typically start with C, D, G, or U
CHANNEL_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{8,}$")
# Dangerous characters for paths: shell metacharacters, control chars, newlines
UNSAFE_PATH_PATTERN = re.compile(r"[;\n\r\0`$|&<>\'\"\\]")


def validate_channel_id(channel_id: str) -> str:
    """Validate and normalize a Slack channel ID.

    Args:
        channel_id: The channel ID to validate

    Returns:
        The validated channel ID (uppercase)

    Raises:
        ValueError: If the channel ID is invalid
    """
    if not channel_id:
        raise ValueError("Channel ID cannot be empty")

    # Normalize to uppercase
    channel_id = channel_id.strip().upper()

    if not CHANNEL_ID_PATTERN.match(channel_id):
        raise ValueError(
            f"Invalid channel ID format: '{channel_id}'. "
            "Channel IDs should be alphanumeric, start with a letter (C, D, G, U), "
            "and be at least 9 characters long (e.g., 'C07R5PAL2L9')."
        )

    return channel_id


def validate_output_dir(output_dir: str) -> str:
    """Validate and normalize an output directory path.

    Args:
        output_dir: The output directory path to validate

    Returns:
        The validated output directory path

    Raises:
        ValueError: If the path contains unsafe characters
    """
    if not output_dir:
        raise ValueError("Output directory cannot be empty")

    output_dir = output_dir.strip()

    # Check for dangerous characters
    if UNSAFE_PATH_PATTERN.search(output_dir):
        raise ValueError(
            f"Output directory contains unsafe characters: '{output_dir}'. "
            "Paths cannot contain: ; \\ ` $ | & < > ' \" or control characters."
        )

    # Check for null bytes (can bypass security checks)
    if "\x00" in output_dir:
        raise ValueError("Output directory cannot contain null bytes")

    return output_dir


def run_command(cmd, description):
    """Run a command and handle errors.

    Args:
        cmd: List of command arguments (e.g., ['slackdump', 'export', '-o', 'dir'])
        description: Human-readable description for status messages
    """
    print(f"📋 {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result.stdout


def export_slack_messages(channel_id, days_back, output_dir):
    """Export messages from Slack using slackdump."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    time_from = start_date.strftime("%Y-%m-%dT00:00:00")
    time_to = end_date.strftime("%Y-%m-%dT23:59:59")

    cmd = [
        "slackdump",
        "export",
        "-time-from",
        time_from,
        "-time-to",
        time_to,
        "-type",
        "standard",
        "-o",
        str(output_dir),
        channel_id,
    ]

    run_command(cmd, f"Exporting Slack messages from {start_date.date()} to {end_date.date()}")
    return output_dir


# ============================================================================
# Slack to Transcript Conversion Functions
# ============================================================================


def load_users(users_file: str) -> Dict[str, Dict[str, Any]]:
    """Load user data from users.json and create a lookup dictionary."""
    print(f"📂 Loading users from {users_file}")

    with open(users_file, "r", encoding="utf-8") as f:
        users_data = json.load(f)

    # Create user_id -> user info mapping
    user_lookup = {}
    for user in users_data:
        user_id = user.get("id")
        profile = user.get("profile", {})

        user_lookup[user_id] = {
            "real_name": user.get("real_name", profile.get("real_name", "Unknown User")),
            "display_name": profile.get("display_name", ""),
            "name": user.get("name", ""),
            "email": profile.get("email", ""),
            "is_bot": user.get("is_bot", False),
        }

    print(f"✅ Loaded {len(user_lookup)} users")
    return user_lookup


def timestamp_to_datetime(ts: str) -> datetime:
    """Convert Slack timestamp to datetime object."""
    return datetime.fromtimestamp(float(ts))


def format_timestamp(ts: str) -> str:
    """Format Slack timestamp for human readability."""
    dt = timestamp_to_datetime(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_user_display(user_id: str, user_lookup: Dict[str, Dict[str, Any]]) -> str:
    """Get the best display name for a user."""
    user = user_lookup.get(user_id, {})

    # Prefer display_name, fallback to real_name, then name, then user_id
    display_name = user.get("display_name") or user.get("real_name") or user.get("name") or user_id

    # Add [Bot] indicator if it's a bot
    if user.get("is_bot"):
        display_name = f"{display_name} [Bot]"

    return display_name


def extract_text_from_message(
    message: Dict[str, Any], user_lookup: Dict[str, Dict[str, Any]]
) -> str:
    """Extract clean text from message, handling various Slack formats with markdown."""
    # Primary text field
    text = message.get("text", "")

    # Ensure code blocks have newlines around them
    # Match ```...``` and ensure newlines before and after
    text = re.sub(r"(?<!\n)(```)", r"\n\1", text)  # Add newline before ``` if not present
    text = re.sub(r"(```[^`]*```)(?!\n)", r"\1\n", text)  # Add newline after ``` if not present

    # Replace user mentions <@U123456> with **@username**
    def replace_mention(match):
        user_id = match.group(1)
        user_name = get_user_display(user_id, user_lookup)
        return f"**@{user_name}**"

    text = re.sub(r"<@([A-Z0-9]+)>", replace_mention, text)

    # Replace channel mentions <#C123456|channel-name> with **#channel-name**
    text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"**#\1**", text)

    # Clean up URLs - keep them but remove the < > wrapper
    text = re.sub(r"<(https?://[^|>]+)(?:\|[^>]+)?>", r"\1", text)

    # Convert inline code: `code` stays as is (Slack uses backticks same as markdown)

    # Convert Slack's bold *text* to markdown **text**
    text = re.sub(r"(?<!\*)\*(?!\*)([^\*]+)\*(?!\*)", r"**\1**", text)

    # Convert Slack's italic _text_ to markdown *text*
    text = re.sub(r"(?<!_)_(?!_)([^_]+)_(?!_)", r"*\1*", text)

    # Convert Slack's strikethrough ~text~ to markdown ~~text~~
    text = re.sub(r"~([^~]+)~", r"~~\1~~", text)

    # Also check if there are attachments with text
    attachments = message.get("attachments", [])
    if attachments:
        attachment_texts = []
        for att in attachments:
            att_text = att.get("text", "")
            if att_text:
                # Apply same replacements to attachment text
                att_text = re.sub(r"<@([A-Z0-9]+)>", replace_mention, att_text)
                att_text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"**#\1**", att_text)
                att_text = re.sub(r"<(https?://[^|>]+)(?:\|[^>]+)?>", r"\1", att_text)
                attachment_texts.append(f"\n> 📎 *Attachment:* {att_text}")
        if attachment_texts:
            text += "\n".join(attachment_texts)

    # Handle files
    files = message.get("files", [])
    if files:
        file_info = []
        for f in files:
            file_name = f.get("name", f.get("title", "unnamed"))
            file_type = f.get("pretty_type", f.get("filetype", ""))
            file_info.append(f"\n📄 *File:* `{file_name}` ({file_type})")
        if file_info:
            text += "\n".join(file_info)

    # Handle reactions
    reactions = message.get("reactions", [])
    if reactions:
        reaction_strs = [f":{r['name']}: ({r['count']})" for r in reactions]
        text += f"\n\n*Reactions:* {', '.join(reaction_strs)}"

    return text


def process_messages_file(
    file_path: str, user_lookup: Dict[str, Dict[str, Any]], include_threads: bool = True
) -> List[str]:
    """Process a single Slack messages JSON file and return formatted transcript lines."""
    print(f"📄 Processing {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    # Sort messages by timestamp
    messages.sort(key=lambda m: float(m.get("ts", "0")))

    transcript_lines = []

    # Group messages by thread
    threads = {}
    standalone_messages = []

    for message in messages:
        thread_ts = message.get("thread_ts")
        ts = message.get("ts")

        if thread_ts and thread_ts != ts:
            # This is a reply in a thread
            if thread_ts not in threads:
                threads[thread_ts] = []
            threads[thread_ts].append(message)
        else:
            standalone_messages.append(message)

    # Process all messages (standalone and thread parents)
    for message in standalone_messages:
        msg_type = message.get("type", "")

        # Skip non-message types
        if msg_type != "message":
            continue

        user_id = message.get("user", "UNKNOWN")
        ts = message.get("ts", "0")
        text = extract_text_from_message(message, user_lookup)

        # Format the message with markdown
        user_display = get_user_display(user_id, user_lookup)
        timestamp_str = format_timestamp(ts)

        transcript_lines.append(f"\n**[{timestamp_str}] {user_display}:**")
        transcript_lines.append(text)

        # Add thread replies if they exist and are requested
        if include_threads and ts in threads:
            transcript_lines.append("\n> **Thread replies:**")
            for reply in sorted(threads[ts], key=lambda m: float(m.get("ts", "0"))):
                reply_user_id = reply.get("user", "UNKNOWN")
                reply_ts = reply.get("ts", "0")
                reply_text = extract_text_from_message(reply, user_lookup)

                reply_user_display = get_user_display(reply_user_id, user_lookup)
                reply_timestamp_str = format_timestamp(reply_ts)

                transcript_lines.append(f"> **[{reply_timestamp_str}] {reply_user_display}:**")
                # Indent reply text with quote markers
                for line in reply_text.split("\n"):
                    transcript_lines.append(f"> {line}")

    print(f"✅ Processed {len(messages)} messages from {file_path}")
    return transcript_lines


def convert_to_transcript(
    export_dir: str, channel_name: str, output_file: str, include_threads: bool = True
):
    """Convert Slack export to markdown transcript."""
    export_path = Path(export_dir)

    # Find the channel directory (should be the only directory besides attachments)
    channel_dirs = [
        d
        for d in export_path.iterdir()
        if d.is_dir() and d.name not in ["attachments", "__uploads"]
    ]

    if not channel_dirs:
        print(f"❌ Error: No channel directory found in {export_dir}")
        sys.exit(1)

    channel_dir = channel_dirs[0]
    users_file = export_path / "users.json"

    # Load users
    try:
        user_lookup = load_users(str(users_file))
    except Exception as e:
        print(f"❌ Failed to load users: {e}")
        sys.exit(1)

    # Find all matching message files
    message_files = glob(str(channel_dir / "*.json"))
    if not message_files:
        print(f"❌ No message files found in {channel_dir}")
        sys.exit(1)

    # Sort files by name (usually by date)
    message_files.sort()
    print(f"📋 Found {len(message_files)} message files")

    # Process all files
    all_transcript_lines = []

    # Add header with markdown
    header_lines = ["# Slack Conversation Transcript", ""]
    if channel_name:
        header_lines.append(f"**Channel:** {channel_name}")
    header_lines.extend(
        [
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Files processed:** {len(message_files)}",
            "",
            "---",
            "",
        ]
    )
    all_transcript_lines.extend(header_lines)

    # Process each file
    for msg_file in message_files:
        file_header = f"\n## 📅 {Path(msg_file).stem}\n"
        all_transcript_lines.append(file_header)

        try:
            lines = process_messages_file(msg_file, user_lookup, include_threads=include_threads)
            all_transcript_lines.extend(lines)
        except Exception as e:
            print(f"❌ Failed to process {msg_file}: {e}")
            continue

    # Add footer
    footer_lines = ["", "---", "", "*End of transcript*"]
    all_transcript_lines.extend(footer_lines)

    # Output
    transcript_text = "\n".join(all_transcript_lines)

    print(f"📝 Writing transcript to {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript_text)
    print(f"✅ Transcript written to {output_file}")

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Generate summary of vLLM CI Slack channel")
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--channel",
        default="C07R5PAL2L9",
        help="Slack channel ID (default: vLLM CI SIG)",
    )
    parser.add_argument("--output-dir", default="vllm_slack_summary", help="Output directory")

    args = parser.parse_args()

    # Validate inputs before use
    try:
        channel_id = validate_channel_id(args.channel)
        output_dir_str = validate_output_dir(args.output_dir)
    except ValueError as e:
        print(f"❌ Input validation error: {e}")
        sys.exit(1)

    print("=" * 60)
    print("vLLM Slack Summary Generator for RHAIIS Team")
    print("=" * 60)

    # Create output directory
    output_dir = Path(output_dir_str)
    output_dir.mkdir(exist_ok=True)

    export_dir = output_dir / "slack_export"
    transcript_file = output_dir / "transcript.md"

    # Step 1: Export Slack messages
    export_slack_messages(channel_id, args.days, str(export_dir))

    # Step 2: Convert to transcript
    convert_to_transcript(str(export_dir), "vLLM CI SIG", str(transcript_file))

    # Step 3: Report locations of generated artifacts
    print(f"\n✅ Transcript generated at: {transcript_file}")
    print(f"📁 Raw Slack export at: {export_dir}")


if __name__ == "__main__":
    main()
