# Edited by Claude Code
"""
Upload Slack Thread to JIRA - Utility Module

This module provides utility functions for the upload-slack-thread skill.
The main workflow is orchestrated by Claude following SKILL.md instructions,
using MCP tools for Slack and JIRA interactions.

This module contains:
- Argument parsing for reference
- Exit codes for error handling
- Helper dataclasses

Note: This is NOT a standalone script. Claude executes the skill by:
1. Reading SKILL.md instructions
2. Calling mcp__slack__conversations_replies to fetch thread
3. Formatting messages as markdown
4. Calling mcp__mcp-atlassian__jira_add_comment to post
"""

from dataclasses import dataclass


# Exit codes per cli-interface.md
EXIT_SUCCESS = 0
EXIT_INVALID_ARGS = 1
EXIT_SLACK_ERROR = 2
EXIT_JIRA_ERROR = 3
EXIT_AUTH_ERROR = 4
EXIT_NOT_FOUND = 5


@dataclass
class SkillArguments:
    """
    Parsed arguments for the upload-slack-thread skill.

    Attributes:
        slack_thread_url: Full Slack thread URL
        ticket_key: JIRA ticket key (optional, auto-detected if not provided)
        summary: Whether to include AI-generated summary
        verbose: Whether to enable verbose logging
    """
    slack_thread_url: str
    ticket_key: str | None = None
    summary: bool = False
    verbose: bool = False


def parse_skill_arguments(args_str: str) -> SkillArguments:
    """
    Parse skill arguments from string.

    Args:
        args_str: Raw arguments string from skill invocation

    Returns:
        SkillArguments with parsed values

    Example:
        >>> args = parse_skill_arguments(
        ...     "https://workspace.slack.com/archives/C123/p456 JN-1234 --summary"
        ... )
        >>> args.slack_thread_url
        'https://workspace.slack.com/archives/C123/p456'
        >>> args.ticket_key
        'JN-1234'
        >>> args.summary
        True
    """
    parts = args_str.split()
    if not parts:
        raise ValueError("No arguments provided")

    url = parts[0]
    ticket_key = None
    summary = False
    verbose = False

    for i, part in enumerate(parts[1:], 1):
        if part in ("--summary", "-s"):
            summary = True
        elif part in ("--verbose", "-v"):
            verbose = True
        elif not part.startswith("-") and ticket_key is None:
            ticket_key = part

    return SkillArguments(
        slack_thread_url=url,
        ticket_key=ticket_key,
        summary=summary,
        verbose=verbose
    )
