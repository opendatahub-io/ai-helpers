# Feature Specification: JIRA Upload Slack Thread

**Feature Branch**: `001-jira-upload-slack-thread`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "Create a new Claude Code skill that fetches a Slack thread and uploads it as a markdown file attachment to a JIRA ticket for documentation and review purposes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Slack Thread to JIRA Ticket (Priority: P1)

A team member who has been discussing a ticket in Slack wants to preserve the full conversation context in JIRA for future reference and audit purposes.

**Why this priority**: This is the core value proposition - preserving Slack discussions alongside formal ticket documentation. Without this, the feature provides no value.

**Independent Test**: Can be fully tested by providing a Slack thread URL and JIRA ticket key, then verifying the markdown file appears as an attachment on the ticket with correctly formatted content.

**Acceptance Scenarios**:

1. **Given** a valid Slack thread URL and JIRA ticket key, **When** the user runs the skill, **Then** a markdown file containing the full thread is uploaded as an attachment to the JIRA ticket
2. **Given** only a Slack thread URL (no ticket key), **When** the user runs the skill, **Then** if the Slack thread has a jira ticket template (e.g. JN-1234) the system will extract the JIRA ticket key and completes the upload after receiving it
2. **Given** only a Slack thread URL (no ticket key), **When** the user runs the skill, **Then** if no jira ticket was given the system prompts for a JIRA ticket key and completes the upload after receiving it
3. **Given** a Slack thread with multiple replies, **When** the export completes, **Then** the markdown file includes all messages in chronological order with user names and timestamps

---

### User Story 2 - Automatic Thread Summary Generation (Priority: P2)

A team member wants to quickly understand the key points of a lengthy Slack discussion without reading every message.

**Why this priority**: Adds significant value by making long threads more accessible, but the feature is still useful without it (full transcript is always available).

**Independent Test**: Can be tested by providing a multi-message Slack thread and verifying the generated markdown includes a concise summary section at the top that captures main topics, decisions, and action items.

**Acceptance Scenarios**:

1. **Given** a Slack thread with 10+ messages, **When** the export completes, **Then** the markdown includes a summary section with 1-2 paragraphs covering main topics, key decisions, and participants
2. **Given** a thread mentioning specific action items, **When** the summary is generated, **Then** those action items are highlighted in the summary

---

### User Story 3 - Handle Various Slack Thread Formats (Priority: P1)

A user provides different formats of Slack URLs (direct thread link, link with reply parameter) and the system correctly parses them.

**Why this priority**: Essential for usability - users shouldn't need to know the "correct" URL format. This is part of the core functionality.

**Independent Test**: Can be tested by providing URLs in different formats and verifying all parse correctly and fetch the same thread content.

**Acceptance Scenarios**:

1. **Given** a direct thread link format `https://workspace.slack.com/archives/C01234567/p1234567890123456`, **When** the skill parses it, **Then** it correctly extracts channel ID and thread timestamp
2. **Given** a thread link with reply parameter `https://workspace.slack.com/archives/C01234567/p1234567890123456?thread_ts=1234567890.123456`, **When** the skill parses it, **Then** it correctly extracts channel ID and thread timestamp
3. **Given** a malformed Slack URL, **When** the skill validates it, **Then** it provides a clear error message explaining the expected format

---

### User Story 4 - Search Conversation Context for JIRA Ticket (Priority: P3)

When a user doesn't provide a JIRA ticket key, the system searches the current conversation for ticket references.

**Why this priority**: Nice-to-have convenience feature that reduces friction, but not essential - user can always provide the ticket key explicitly.

**Independent Test**: Can be tested by mentioning a JIRA ticket key earlier in the conversation, then running the skill without specifying a ticket and verifying it auto-detects the correct ticket.

**Acceptance Scenarios**:

1. **Given** a JIRA ticket key mentioned in a slack conversation thread, **When** the user runs the skill without specifying a ticket, **Then** the system auto-detects and uses that ticket key
2. **Given** no JIRA ticket references in conversation, **When** the user runs the skill without specifying a ticket, **Then** the system prompts the user to provide one

---

- What happens when the Slack MCP server is not configured or unavailable?
### Edge Cases

- What happens when the Slack API token lacks required permissions to read the thread?
- What happens when the JIRA API token lacks permission to attach files to the ticket?
- How does the system handle rate limiting from Slack API?
- What happens when a Slack thread is very long (100+ messages)?
- How does the system handle threads containing files/attachments (should metadata be included)?
- What happens when user IDs in Slack cannot be resolved to display names?
- How does the system handle deleted messages or private channels?
- What happens when the JIRA ticket doesn't exist?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a Slack thread URL as required input in format `https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP` or with `thread_ts` parameter
- **FR-002**: System MUST parse Slack URLs to extract workspace domain, channel ID, and thread timestamp
- **FR-003**: System MUST validate Slack URL format before attempting API calls and provide clear error messages for invalid formats
- **FR-004**: System MUST accept an optional JIRA ticket key as input
- **FR-005**: System MUST prompt user for JIRA ticket key if not provided and not found in conversation context
- **FR-006**: System MUST search conversation history for JIRA ticket references when ticket key not explicitly provided
- **FR-007**: System MUST interact with Slack via the Slack MCP server for fetching thread data
- **FR-008**: System MUST authenticate to JIRA API using token from `JIRA_API_TOKEN` environment variable
- **FR-009**: System MUST fetch all messages in the Slack thread including parent message and all replies
- **FR-010**: System MUST resolve Slack user IDs to display names for all message authors
- **FR-011**: System MUST format thread content as markdown with structure: header (metadata), full transcript with user names and timestamps
- **FR-013**: System MUST save formatted markdown to temporary file named `slack-thread-{ticket-key}-{timestamp}.md` in `/tmp/claude/` directory 
- **FR-014**: System MUST upload markdown file as a comment to specified JIRA ticket at the jira project (possibly paste from clipboard)
- **FR-015**: System MUST delete temporary markdown file after upload attempt (success or failure)
- **FR-016**: System MUST provide clear success message with direct link to JIRA ticket comment upon successful upload
- **FR-017**: System MUST provide clear error messages with troubleshooting guidance for common failures (missing tokens, invalid permissions, rate limiting, MCP server unavailable, etc.)
- **FR-018**: System MUST handle Slack API rate limiting gracefully with appropriate retry logic or clear error messages
- **FR-019**: System MUST NOT log or display API token values
- **FR-020**: System MUST include metadata for file attachments mentioned in thread (file name, type) but NOT download actual files
- **FR-021**: System MUST preserve message chronological order in markdown output
- **FR-022**: System MUST include thread metadata in markdown header: export timestamp, ticket URL, original Slack URL, channel name
- **FR-023**: System MUST follow ai-helpers repository development guidelines and skill development patterns

### Key Entities

- **Slack Thread**: Represents a conversation in Slack with a parent message and zero or more reply messages, identified by channel ID and thread timestamp
- **Thread Message**: Individual message within a thread containing user ID, timestamp, text content, and optional file attachments
- **JIRA Ticket**: Issue tracking record identified by ticket key (e.g., AIPCC-1234 or JN-1234) where thread export will be attached
- **Markdown Export**: Formatted document containing thread link, metadata, AI summary, and full message transcript

## Extra Requirements *(second stage)*

### Functional Requirements Extra 
- **FR-100**: System will prompt for a user directory to  save the formatted markdown to temporary files
- **FR-101**: System can allwo to the user to save the  temporary markdown file after upload attempt (success or failure)
- **FR-102**: System will upload markdown file as attachment to specified JIRA ticket at the jira project
- **FR-011**: System will format thread content as markdown with structure: header (metadata), AI-generated summary
- **FR-103**: System will generate AI summary - if flaged - with the thread including main topics, key decisions, action items, and participants (1-3 paragraphs maximum)


## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully export a Slack thread to JIRA in under 30 seconds from skill invocation to completion
- **SC-002**: System correctly parses and processes 100% of valid Slack thread URL formats (direct links and links with thread_ts parameter)
- **SC-003**: Generated markdown files are properly formatted and readable in JIRA's markdown renderer with no rendering errors
- **SC-004**: AI-generated summaries accurately capture main topics and key decisions in 90% of threads (as validated by user review)
- **SC-005**: System provides actionable error messages that allow users to resolve issues (missing tokens, invalid permissions, MCP server issues) without developer intervention
- **SC-006**: Exported thread transcripts include all messages from the original Slack thread with no missing content
- **SC-007**: Users successfully complete the full workflow on first attempt in 80% of use cases (with valid inputs and proper authentication)

## Assumptions

- Users have necessary permissions to read Slack threads they attempt to export
- Users have JIRA permissions to update comments in tickets they reference
- Users have JIRA permissions to attach files to tickets they reference
- Slack MCP server is properly configured and available
- JIRA API token has attachment creation permissions
- Python 3 and `uv` are available in the execution environment
- Standard Slack workspace URL patterns are used (no custom vanity URLs requiring special handling)
- Thread content is text-based; embedded media/files are referenced but not downloaded
- Reasonable thread size (under 500 messages) - extremely long threads may require chunking or truncation
- Network connectivity to both Slack (via MCP) and JIRA APIs
- The existing `scripts/upload_chat_log.py` pattern can be reused or adapted for uploading to JIRA

## Dependencies

- Slack MCP server from https://github.com/redhat-community-ai-tools/slack-mcp for Slack API interaction
- JIRA API availability and access at https://jounce.atlassian.net/
- JIRA API token from `JIRA_API_TOKEN` environment variable (or ask for location of .env file)
- Python environment with `uv` package manager
- AI summarization capability (Claude or equivalent)
- Existing JIRA upload utilities or patterns from `scripts/upload_chat_log.py`
- Repository development guidelines and skill development patterns from ai-helpers repo

## Development Guidelines

- Skill MUST be developed following the ai-helpers repository conventions and patterns
- Skill MUST follow existing skill development patterns in the repository
- Code MUST adhere to repository coding standards and style guides
- Implementation MUST be consistent with other skills in the ai-helpers repository
- Testing MUST follow repository testing practices

## Out of Scope

- Downloading and uploading actual file attachments from Slack thread (only metadata is included)
- Support for Slack Enterprise Grid multi-workspace scenarios
- Real-time sync or automatic updates when thread continues after export
- Exporting multiple threads in a single operation
- Custom formatting options or export templates
- Editing or filtering thread content before upload
- Support for Slack reactions beyond basic metadata
- Direct Slack SDK usage (must use Slack MCP server instead)
- Automatic detection of which Slack thread to export (must be explicitly provided)
