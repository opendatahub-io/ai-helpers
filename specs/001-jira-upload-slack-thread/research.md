# Research: JIRA Upload Slack Thread

**Feature**: Upload Slack Thread to JIRA  
**Date**: 2026-01-26  
**Phase**: 0 (Outline & Research)  

## Research Overview

This document consolidates research findings for implementing a skill that fetches Slack threads via Slack MCP server and uploads them as JIRA comments.  

## Key Research Areas

### 1. Slack Thread Fetching via slackdump

**Decision**: Use slackdump CLI tool for all Slack thread fetching

**Rationale**:
- slackdump provides robust Slack export functionality via CLI
- Handles authentication via workspace configuration
- Exports messages to JSON format for easy processing
- Proven pattern used in vllm-slack-summary skill
- Eliminates need for direct Slack SDK or MCP dependencies

**Alternatives Considered**:
- **Slack MCP server**: Considered but slackdump provides more robust export
- **slack-sdk Python library**: Rejected to avoid direct SDK dependencies
- **Direct Slack API HTTP calls**: Rejected due to added complexity in auth handling

**Implementation Notes**:
- slackdump CLI: <https://github.com/rusq/slackdump>
- Auth: `slackdump workspace add`
- Export thread: `slackdump -export-type mattermost -files=false -t "{channel_id}:{thread_ts}" -o /tmp/claude/slack_thread_export`
- Parse exported JSON for messages and users.json for user resolution
- URL format: `https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP`
- Thread timestamp extraction: convert `p` format to decimal timestamp  

### 2. JIRA Comment Posting (vs Attachments)

**Decision**: Post markdown as JIRA comment using JIRA MCP server

**Rationale**:
- Clarification session confirmed: upload as comment (inline) rather than attachment
- Comments are immediately visible in ticket timeline
- Matches user expectation for conversation logs
- MCP server provides consistent pattern with Slack integration

**Alternatives Considered**:
- **File attachment**: Rejected per clarification (Q1: "Upload as JIRA ticket comment")
- **Both comment AND attachment**: Rejected as unnecessary duplication
- **jira Python library**: Rejected in favor of MCP-only approach for consistency

**Implementation Notes**:
- JIRA MCP server exposes tools via MCP protocol
    - Tools include: `jira_add_comment`, `jira_get_issue`, etc.
- All JIRA interactions use MCP server exclusively (no jira Python library fallback)
- Authentication: JIRA_API_TOKEN environment variable (used by MCP server)
- JIRA server: https://jounce.atlassian.net/ (configurable via JIRA_PROJECT_URL)
- Comments support markdown formatting  

### 3. JIRA Ticket Key Extraction Pattern

**Decision**: Use regex pattern `[A-Z]+-\d+` to extract ticket keys from Slack thread content  

**Rationale**:  
- Clarification session defined standard JIRA format  
- Covers all JIRA ticket key formats (project prefix + number)  
- Examples: JN-1234, AIPCC-1234, RHEL-9876  
- When multiple keys found, use first occurrence in chronological order (Q4 clarification)  

**Alternatives Considered**:  
- **More restrictive patterns** (e.g., specific project prefixes): Rejected as too limiting  
- **Looser patterns** (e.g., any word-number combo): Rejected as too many false positives  

**Implementation Notes**:  
- Regex: `r'[A-Z]+-\d+'`  
- Search order: chronological (parent message → replies in order)  
- Return first match only  
- Case-sensitive (uppercase letters required)  

### 4. Message Truncation Strategy

**Decision**: Truncate at 50 messages with warning in markdown output  

**Rationale**:  
- Clarification session reduced limit from 500 to 50 messages (Q5)  
- Balance between completeness and performance  
- Prevents timeout issues and excessive API calls  
- Warns users about truncation for awareness  

**Alternatives Considered**:  
- **No limit**: Rejected due to timeout/memory concerns  
- **Reject threads over 50**: Rejected as users lose all data  
- **Chunk into multiple comments**: Rejected as added complexity  

**Implementation Notes**:  
- Fetch messages in chronological order  
- If count > 50, take first 50 messages  
- Add warning at top of markdown: "⚠️ Thread truncated: showing 50 of {total_count} messages"  
- Include total message count in warning  

### 5. AI Summary Generation

**Decision**: Optional feature via `--summary` flag, disabled by default  

**Rationale**:  
- Clarification session defined as optional with flag (Q2)  
- Default OFF reduces latency for simple exports  
- Uses Claude AI (via MCP tools or direct API) when enabled  
- 1-2 paragraphs maximum per spec  

**Alternatives Considered**:  
- **Always generate**: Rejected per clarification (default disabled)  
- **Never generate**: Rejected as User Story 2 is P2 priority  

**Implementation Notes**:  
- CLI flag: `--ai-summary` or `-s`  
- When enabled, prepend AI-generated summary before full transcript  
- Summary format: 1-2 paragraphs covering topics, decisions, participants, action items  
- Use Claude API or MCP tools for generation  
- If summary generation fails, continue with transcript only (non-blocking)  

### 6. Error Handling Best Practices

**Decision**: Follow text I/O pattern with actionable error messages  

**Rationale**:  
- Constitution principle VII: Observability & Debugging  
- Errors to stderr, success output to stdout  
- inspire from existing `upload_chat_log.py` pattern  

**Implementation Pattern**:  
```python
# Success output to stdout
print(f"✓ Successfully posted to {ticket_key}")
print(f"  View: {jira_url}/browse/{ticket_key}")

# Errors to stderr with context
print(f"ERROR: {specific_issue}", file=sys.stderr)
print("\nPossible reasons:", file=sys.stderr)
print("  - {reason 1}", file=sys.stderr)
print("  - {reason 2}", file=sys.stderr)
sys.exit(1)
```

**Error Categories**:  
- **Configuration**: Missing tokens, MCP server unavailable  
- **Input Validation**: Invalid URL format, malformed ticket key  
- **API Errors**: Rate limiting, permission denied, resource not found  
- **Network**: Connection failures, timeouts  

### 7. PEP 723 Inline Script Metadata

**Decision**: Use PEP 723 format with `uv run --script` shebang  

**Rationale**:  
- Matches existing skill pattern (upload_chat_log.py)  
- UV handles dependency installation automatically  
- No separate requirements.txt needed  
- Constitution requires UV for package management  

**Implementation Template**:  
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "jira>=3.0.0",
# ]
# ///
```

**Dependencies Required**:  
- No Slack SDK (using MCP server tools instead)  
- No JIRA SDK (using MCP server tools instead)  

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Language | Python | 3.13 | Project standard, constitution requirement |
| Package Manager | UV | latest | Constitution mandate (Principle VI) |
| Slack Integration | slackdump CLI | latest | Proven pattern from vllm-slack-summary |
| JIRA Integration | JIRA MCP Server | latest | MCP tools for comment posting |
| Testing | pytest | latest | Constitution requirement |
| Type Checking | mypy | latest | Constitution requirement (strict mode) |
| Linting | ruff | latest | Constitution requirement |

## Performance Considerations

| Metric | Target | Strategy |
|--------|--------|----------|
| URL Parsing | <200ms | Regex compilation, no network calls |
| slackdump Export | <15s | CLI handles connection pooling |
| JIRA Comment Post | <5s | Single MCP API call |
| Total Workflow | <30s | Parallel where possible, fail fast |
| Memory Usage | <100MB | Stream messages, don't load all in memory |

## Security Considerations

1. **Token Storage**: Read from environment variables only (JIRA_API_TOKEN)
2. **Token Logging**: Never log or display token values (FR-020)
3. **Input Validation**: Sanitize URLs and ticket keys before API calls
4. **Error Messages**: Don't expose internal details in user-facing errors
5. **slackdump Auth**: Rely on slackdump's workspace authentication handling  

## Open Questions (All Resolved)

All technical unknowns have been resolved through clarification session and research. No blocking questions remain.  

## Next Steps

Proceed to Phase 1: Design & Contracts
- Create data-model.md (entities: SlackThread, ThreadMessage, MarkdownExport, JIRATicket)
- Generate CLI contract in contracts/cli-interface.md
- Create quickstart.md with usage examples
- Update agent context with slackdump patterns  

### 8. JIRA MCP Server Integration

**Decision**: Use JIRA MCP server for JIRA API interactions (not jira Python library)  

**Rationale**:  
- Consistent with Slack MCP pattern  
- MCP servers provide standardized interface  
- Simplifies authentication and error handling  
- Reduces direct library dependencies  

**Alternatives Considered**:  
- **jira Python library**: Initially planned, but MCP pattern preferred for consistency  
- **Direct JIRA REST API**: Rejected due to auth complexity  

**Implementation Notes**:  
- JIRA MCP server provides tools for ticket operations  
- Tools include: `jira_add_comment`, `jira_get_issue`, etc.  
- JIRA_PROJECT_URL loaded from .env file (not hardcoded)  
- Pattern: Read JIRA_PROJECT_URL from environment or .env file  

**Configuration**:  
```bash
# .env file in the system or in the root project
JIRA_PROJECT_URL=https://jounce.atlassian.net/
JIRA_API_TOKEN=your-api-token-here
```

**Update**: JIRA URL should be configurable via .env, not hardcoded to specific instance.  

---

### 9. Message Consolidation for Readability

**Decision**: Merge consecutive messages from the same user into single blocks  

**Rationale**:  
- Improves readability in JIRA comments  
- Reduces visual clutter  
- Preserves conversation flow  
- Common pattern in chat exports  

**Alternatives Considered**:  
- **Keep all messages separate**: Rejected as too verbose  
- **Merge all messages from same user**: Rejected as loses chronological context  

**Implementation**:  
- Iterate through messages in order  
- If current message has same user_id as previous, append text with double newline  
- Keep timestamp of first message in merged block  
- Preserve file attachments across merged messages  

**Example Logic**:  
```python
merged_messages = []
for msg in messages:
    if merged_messages and msg.user_id == merged_messages[-1].user_id:
        merged_messages[-1].text += f"\n\n{msg.text}"
    else:
        merged_messages.append(msg)
```
