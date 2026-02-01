# Edited by Claude Code
"""
JIRA comment data models.

This module provides data models for JIRA comments.
Actual posting is handled by Claude using the JIRA MCP server's jira_add_comment tool.
"""

from dataclasses import dataclass


@dataclass
class JIRAComment:
    """
    Represents a comment to be posted to JIRA.

    Attributes:
        ticket_key: JIRA ticket identifier (e.g., "JN-1234")
        body: Comment content (markdown formatted)
        comment_id: JIRA comment ID (set after successful post)
    """

    ticket_key: str
    body: str
    comment_id: str | None = None

    def __post_init__(self):
        """Validate comment data."""
        if not self.body:
            raise ValueError("Comment body must not be empty")

        if not self.ticket_key:
            raise ValueError("Ticket key must not be empty")
