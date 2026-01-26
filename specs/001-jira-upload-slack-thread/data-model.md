# Data Model: JIRA Upload Slack Thread

**Feature**: Upload Slack Thread to JIRA  
**Date**: 2026-01-26  
**Phase**: 1 (Design & Contracts)  

## Overview

This document defines the data entities and their relationships for the Slack thread to JIRA comment upload workflow. All entities are value objects (no persistence layer) used for in-memory processing.  

## Core Entities

### SlackThreadURL

**Purpose**: Represents a parsed and validated Slack thread URL  

**Attributes**:  
- `raw_url: str` - Original URL provided by user  
- `workspace: str` - Slack workspace identifier (e.g., "redhat-internal")  
- `channel_id: str` - Channel ID (e.g., "C09Q8MD1V0Q")  
- `thread_ts: str` - Thread timestamp in decimal format (e.g., "1769333522.823869")  

**Validation Rules**:  
- `raw_url` must match pattern: `https://*.slack.com/archives/{CHANNEL_ID}/p{TIMESTAMP}`  
- `channel_id` must match `C[A-Z0-9]+` pattern  
- `thread_ts` must be convertible from `p{TIMESTAMP}` format (remove 'p', insert decimal point)  

**Relationships**:  
- One SlackThreadURL → One SlackThread (via fetch operation)  

**Example**:  
```python
SlackThreadURL(
    raw_url="https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869",
    workspace="redhat-internal",
    channel_id="C09Q8MD1V0Q",
    thread_ts="1769333522.823869"
)
```

---  

### ThreadMessage

**Purpose**: Represents a single message within a Slack thread  

**Attributes**:  
- `user_id: str` - Slack user ID (e.g., "U01ABC123")  
- `user_name: str` - Display name resolved from user ID  
- `timestamp: str` - Message timestamp  
- `text: str` - Message content (markdown-formatted)  
- `is_parent: bool` - True if this is the thread's parent message  
- `attachments: list[AttachmentMetadata]` - File attachment metadata (if any)  

**Validation Rules**:  
- `user_id` must not be empty  
- `timestamp` must be valid Slack timestamp format  
- `text` must be present (can be empty string for file-only messages)  
- `user_name` defaults to user_id if resolution fails  

**Relationships**:  
- Many ThreadMessages → One SlackThread  
- One ThreadMessage → Many AttachmentMetadata (0..*)  

**Example**:  
```python
ThreadMessage(
    user_id="U01ABC123",
    user_name="John Doe",
    timestamp="1769333522.823869",
    text="Let's discuss the JIRA ticket JN-1234",
    is_parent=True,
    attachments=[]
)
```

---  

### AttachmentMetadata

**Purpose**: Represents metadata about a file attachment in a Slack message  

**Attributes**:  
- `filename: str` - Name of the attached file  
- `filetype: str` - File type/extension  
- `size: int | None` - File size in bytes (if available)  

**Validation Rules**:  
- `filename` must not be empty  
- `filetype` should be extracted from filename if not provided  

**Relationships**:  
- One AttachmentMetadata → One ThreadMessage (belongs to)  

**Example**:  
```python
AttachmentMetadata(
    filename="screenshot.png",
    filetype="png",
    size=102400
)
```

---  

### SlackThread

**Purpose**: Represents a complete Slack thread with all messages  

**Attributes**:  
- `channel_id: str` - Channel containing the thread  
- `channel_name: str | None` - Human-readable channel name  
- `thread_ts: str` - Thread timestamp  
- `messages: list[ThreadMessage]` - All messages in chronological order  
- `total_message_count: int` - Total messages (may be > len(messages) if truncated)  
- `is_truncated: bool` - True if thread exceeded 50 message limit  

**Validation Rules**:  
- `messages` must have at least 1 element (the parent message)  
- `messages[0].is_parent` must be True  
- `total_message_count` >= len(messages)  
- If `is_truncated` is True, len(messages) should be 50  

**Relationships**:  
- One SlackThread → Many ThreadMessages (1..50)  
- One SlackThread → One MarkdownExport (via formatting operation)  

**Example**:  
```python
SlackThread(
    channel_id="C09Q8MD1V0Q",
    channel_name="team-discussion",
    thread_ts="1769333522.823869",
    messages=[...],  # List of ThreadMessage objects
    total_message_count=45,
    is_truncated=False
)
```

---  

### JIRATicketKey

**Purpose**: Represents a validated JIRA ticket identifier  

**Attributes**:  
- `raw_key: str` - Original ticket key string  
- `project: str` - Project prefix (e.g., "JN", "AIPCC")  
- `number: int` - Ticket number  

**Validation Rules**:  
- `raw_key` must match pattern: `[A-Z]+-\d+`  
- `project` must be uppercase letters only  
- `number` must be positive integer  

**Relationships**:  
- One JIRATicketKey → One JIRAComment (target for upload)  

**Example**:  
```python
JIRATicketKey(
    raw_key="JN-1234",
    project="JN",
    number=1234
)
```

---  

### MarkdownExport

**Purpose**: Represents the formatted markdown document ready for JIRA upload  

**Attributes**:  
- `ticket_key: str` - Target JIRA ticket (e.g., "JN-1234")  
- `thread_url: str` - Original Slack thread URL  
- `channel_name: str` - Slack channel name  
- `export_timestamp: str` - ISO 8601 timestamp of export  
- `summary: str | None` - AI-generated summary (if enabled)  
- `transcript: str` - Formatted message transcript  
- `is_truncated: bool` - Whether thread was truncated  
- `total_message_count: int` - Total messages in thread  
- `included_message_count: int` - Messages included in export  

**Validation Rules**:  
- `ticket_key` must be valid JIRA format  
- `thread_url` must be valid Slack URL  
- `export_timestamp` must be ISO 8601 format  
- `transcript` must not be empty  
- If `is_truncated`, include truncation warning in content  

**Derived Properties**:  
- `full_content: str` - Combines header + summary + transcript into final markdown  

**Relationships**:  
- One MarkdownExport → One JIRAComment (via upload operation)  

**Example**:  
```python
MarkdownExport(
    ticket_key="JN-1234",
    thread_url="https://redhat-internal.slack.com/archives/C09Q8MD1V0Q/p1769333522823869",
    channel_name="team-discussion",
    export_timestamp="2026-01-26T10:30:00Z",
    summary="Discussion about implementing feature X...",  # Optional
    transcript="### John Doe - 2026-01-26 10:15\nLet's discuss...",
    is_truncated=False,
    total_message_count=45,
    included_message_count=45
)
```

---  

### JIRAComment

**Purpose**: Represents a comment to be posted to JIRA  

**Attributes**:  
- `ticket_key: str` - JIRA ticket identifier  
- `body: str` - Comment content (markdown formatted)  
- `comment_id: str | None` - JIRA comment ID (set after successful post)  

**Validation Rules**:  
- `ticket_key` must be valid JIRA format  
- `body` must not be empty  
- `comment_id` is None before posting, set after successful API call  

**Relationships**:  
- One JIRAComment → One JIRA Ticket (external system)  

**Example**:  
```python
JIRAComment(
    ticket_key="JN-1234",
    body="# Slack Thread Export\n...",
    comment_id=None  # Set after posting
)
```

## Entity Relationships Diagram

```text
SlackThreadURL
    ↓ (parse & fetch)
SlackThread
    ├── ThreadMessage (1..50)
    │   └── AttachmentMetadata (0..*)
    ↓ (format)
MarkdownExport
    ↓ (post)
JIRAComment
    ↓ (upload)
JIRA Ticket (external)

JIRATicketKey
    ↓ (extract from thread or user input)
Used by → MarkdownExport, JIRAComment
```

## State Transitions

### Workflow State Machine

```text
[Start]
    ↓
[Parse URL] → SlackThreadURL
    ↓
[Fetch Messages via MCP] → SlackThread
    ↓
[Extract/Prompt Ticket Key] → JIRATicketKey
    ↓
[Format Markdown] → MarkdownExport
    ↓ (optional)
[Generate AI Summary] → MarkdownExport (with summary)
    ↓
[Post to JIRA] → JIRAComment
    ↓
[Success/Error] → [End]
```

## Data Validation Strategy

All entities use dataclasses with type hints and validation in `__post_init__`:  

```python
from dataclasses import dataclass
import re

@dataclass
class JIRATicketKey:
    raw_key: str
    
    def __post_init__(self):
        if not re.match(r'^[A-Z]+-\d+$', self.raw_key):
            raise ValueError(f"Invalid JIRA ticket key format: {self.raw_key}")
        parts = self.raw_key.split('-')
        self.project = parts[0]
        self.number = int(parts[1])
```

## Error Handling

Each entity validation failure raises specific exceptions:  
- `InvalidURLError` - SlackThreadURL validation fails  
- `InvalidTicketKeyError` - JIRATicketKey validation fails  
- `MessageValidationError` - ThreadMessage validation fails  
- `EmptyThreadError` - SlackThread has no messages  

All exceptions include actionable error messages for users.  

## Message Merging Strategy

### Consecutive Message Consolidation

**Rule**: When multiple consecutive messages in a thread are from the same user, merge them into a single message block in the markdown output.  

**Rationale**:  
- Improves readability of exported threads  
- Reduces visual clutter in JIRA comments  
- Preserves conversation flow while maintaining context  

**Implementation**:  
```python
def merge_consecutive_messages(messages: list[ThreadMessage]) -> list[ThreadMessage]:
    """Merge consecutive messages from same user."""
    if not messages:
        return []
    
    merged = [messages[0]]
    for msg in messages[1:]:
        if msg.user_id == merged[-1].user_id:
            # Merge: append text with newline separator
            merged[-1].text += f"\n\n{msg.text}"
            # Update timestamp to latest
            merged[-1].timestamp = msg.timestamp
        else:
            merged.append(msg)
    
    return merged
```

**Example**:  

**Before Merging** (3 separate messages):  
```markdown
### John Doe - 2026-01-26 10:15:00
Let me share my thoughts

### John Doe - 2026-01-26 10:15:30
Actually, I have more to add

### John Doe - 2026-01-26 10:16:00
And one more thing...

### Jane Smith - 2026-01-26 10:17:00
Thanks John, that's helpful
```

**After Merging** (consolidated):  
```markdown
### John Doe - 2026-01-26 10:15:00
Let me share my thoughts

Actually, I have more to add

And one more thing...

### Jane Smith - 2026-01-26 10:17:00
Thanks John, that's helpful
```

**Edge Cases**:  
- Empty messages: Skip empty text, don't merge  
- File-only messages: Preserve as separate if no text  
- Timestamp handling: Use timestamp of first message in merged block  
