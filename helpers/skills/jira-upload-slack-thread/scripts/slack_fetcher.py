# Edited by Claude Code
"""
Slack thread data models.

This module provides data models for Slack thread messages.
Actual fetching is handled by Claude using the Slack MCP server tools.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Maximum number of messages to include in a thread export
# Threads longer than this will be truncated with a warning
MAX_THREAD_MESSAGES = 50


class EmptyThreadError(ValueError):
    """Raised when a Slack thread has no messages."""
    pass


@dataclass
class AttachmentMetadata:
    """
    Represents metadata about a file attachment in a Slack message.

    Attributes:
        filename: Name of the attached file
        filetype: File type/extension
        url: URL to access the attachment (if available)
        size: File size in bytes (if available)
    """
    filename: str
    filetype: str
    url: str | None = None
    size: int | None = None

    def __post_init__(self):
        """Validate attachment metadata."""
        if not self.filename:
            raise ValueError("Attachment filename must not be empty")

        # Extract filetype from filename if not provided
        if not self.filetype and '.' in self.filename:
            self.filetype = self.filename.rsplit('.', 1)[1]


@dataclass
class ThreadMessage:
    """
    Represents a single message within a Slack thread.

    Attributes:
        user_id: Slack user ID (e.g., "U01ABC123")
        user_name: Display name resolved from user ID
        timestamp: Message timestamp
        text: Message content (markdown-formatted)
        is_parent: True if this is the thread's parent message
        attachments: File attachment metadata (if any)
    """
    user_id: str
    user_name: str
    timestamp: str
    text: str
    is_parent: bool = False
    attachments: list[AttachmentMetadata] | None = None

    def __post_init__(self):
        """Validate message data."""
        if not self.user_id:
            raise ValueError("User ID must not be empty")

        if not self.timestamp:
            raise ValueError("Timestamp must not be empty")

        # Default user_name to user_id if resolution failed
        if not self.user_name:
            logger.warning(
                f"Could not resolve user_id {self.user_id} to display name. "
                f"Using user_id as fallback. This may indicate insufficient Slack permissions."
            )
            self.user_name = self.user_id

        # Ensure attachments is a list
        if self.attachments is None:
            self.attachments = []


@dataclass
class SlackThread:
    """
    Represents a complete Slack thread with all messages.

    Attributes:
        channel_id: Channel containing the thread
        channel_name: Human-readable channel name
        thread_ts: Thread timestamp
        messages: All messages in chronological order
        total_message_count: Total messages (may be > len(messages) if truncated)
        is_truncated: True if thread exceeded 50 message limit
    """
    channel_id: str
    channel_name: str | None
    thread_ts: str
    messages: list[ThreadMessage]
    total_message_count: int
    is_truncated: bool = False

    def __post_init__(self):
        """Validate thread data."""
        if not self.messages:
            raise EmptyThreadError("Thread must have at least one message (parent)")

        if not self.messages[0].is_parent:
            raise ValueError("First message must be marked as parent")

        if self.total_message_count < len(self.messages):
            raise ValueError(
                f"Total message count ({self.total_message_count}) cannot be less than "
                f"included messages ({len(self.messages)})"
            )

        # Validate message count limits
        if len(self.messages) > MAX_THREAD_MESSAGES:
            raise ValueError(
                f"Message list cannot exceed {MAX_THREAD_MESSAGES} items "
                f"(got {len(self.messages)})"
            )

        # Validate truncation consistency
        if self.is_truncated and self.total_message_count <= len(self.messages):
            raise ValueError(
                f"Truncated threads must have total_message_count > included messages "
                f"(got total={self.total_message_count}, included={len(self.messages)})"
            )
