#!/usr/bin/env python3
"""
Generate Slack Transcript for vLLM Weekly Summary

Exports Slack channel messages and converts them to a markdown transcript
for Claude to summarize.

Prerequisites:
    - slackdump: CLI tool for exporting Slack messages (https://github.com/rusq/slackdump)
    - slack_to_transcript.py: Must exist at the project root (4 directories up from this script)

What this script does:
    1. Exports messages from a Slack channel for the specified time period using slackdump
    2. Converts the JSON export to a readable markdown transcript
    3. Outputs the transcript with a summary prompt for Claude to process

Usage:
    python generate_transcript.py [--days N] [--channel CHANNEL_ID] [--output-dir DIR]

Arguments:
    --days        Number of days to look back (default: 7)
    --channel     Slack channel ID (default: C07R5PAL2L9 for vLLM CI SIG)
    --output-dir  Directory for output files (default: vllm_weekly_summary)

Output:
    Creates a directory containing:
    - slack_export/: Raw slackdump export data
    - transcript.md: Formatted markdown transcript of conversations
"""

import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import argparse


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"📋 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result.stdout


def export_slack_messages(channel_id, days_back, output_dir):
    """Export messages from Slack using slackdump."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    time_from = start_date.strftime('%Y-%m-%dT00:00:00')
    time_to = end_date.strftime('%Y-%m-%dT23:59:59')

    cmd = (
        f'slackdump export '
        f'-time-from {time_from} '
        f'-time-to {time_to} '
        f'-type standard '
        f'-o {output_dir} '
        f'{channel_id}'
    )

    run_command(cmd, f"Exporting Slack messages from {start_date.date()} to {end_date.date()}")
    return output_dir


def convert_to_transcript(export_dir, channel_name, output_file):
    """Convert Slack export to markdown transcript."""
    # Navigate from scripts/ -> vllm-weekly-summary/ -> skills/ -> .claude/ -> project_root/
    project_root = Path(__file__).parent.parent.parent.parent.parent
    transcript_script = project_root / "slack_to_transcript.py"

    if not transcript_script.exists():
        print(f"❌ Error: slack_to_transcript.py not found at {transcript_script}")
        sys.exit(1)

    # Find the channel directory (should be the only directory besides attachments)
    export_path = Path(export_dir)
    channel_dirs = [d for d in export_path.iterdir() if d.is_dir() and d.name not in ['attachments', '__uploads']]

    if not channel_dirs:
        print(f"❌ Error: No channel directory found in {export_dir}")
        sys.exit(1)

    channel_dir = channel_dirs[0]
    messages_pattern = f"{channel_dir}/*.json"
    users_file = export_path / "users.json"

    cmd = (
        f'{transcript_script} '
        f'-m "{messages_pattern}" '
        f'-u {users_file} '
        f'-o {output_file} '
        f'--channel-name "{channel_name}"'
    )

    run_command(cmd, "Converting to transcript")
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Generate weekly summary of vLLM CI Slack channel')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back (default: 7)')
    parser.add_argument('--channel', default='C07R5PAL2L9', help='Slack channel ID (default: vLLM CI SIG)')
    parser.add_argument('--output-dir', default='vllm_weekly_summary', help='Output directory')

    args = parser.parse_args()

    print("=" * 60)
    print("vLLM Weekly Summary Generator for RHAIIS Team")
    print("=" * 60)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    export_dir = output_dir / "slack_export"
    transcript_file = output_dir / "transcript.md"

    # Step 1: Export Slack messages
    export_slack_messages(args.channel, args.days, str(export_dir))

    # Step 2: Convert to transcript
    convert_to_transcript(str(export_dir), "vLLM CI SIG", str(transcript_file))

    # Step 3: Read and output transcript for Claude to summarize
    print(f"\n✅ Transcript generated: {transcript_file}")
    print(f"📁 Slack export: {export_dir}")

    # Read the transcript
    with open(transcript_file, 'r') as f:
        transcript_content = f.read()

    # Output structured data for Claude Code to process
    print("\n" + "=" * 60)
    print("TRANSCRIPT READY - PLEASE SUMMARIZE FOR RHAIIS TEAM")
    print("=" * 60 + "\n")

    print("CONTEXT:")
    print("- vLLM is an open-source project for efficient LLM serving")
    print("- Red Hat builds and releases a midstream version called RHAIIS (Red Hat AI Inference Server)")
    print("- The CI SIG channel discusses CI/CD infrastructure, test failures, build issues, and release engineering")
    print("\nPLEASE PROVIDE A SUMMARY WITH THESE SECTIONS:")
    print("1. Executive Summary (2-3 sentences)")
    print("2. Key Issues & Resolutions")
    print("3. CI/CD Infrastructure Changes")
    print("4. Test Failures & Flakes")
    print("5. Upstream Dependencies & Breaking Changes")
    print("6. Action Items for Red Hat Team")
    print("7. Notable Contributors & Discussions")

    print("\n" + "=" * 60)
    print("FULL TRANSCRIPT:")
    print("=" * 60 + "\n")
    print(transcript_content)


if __name__ == "__main__":
    main()
