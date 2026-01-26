# Implementation Plan: JIRA Upload Slack Thread

**Branch**: `001-jira-upload-slack-thread` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-jira-upload-slack-thread/spec.md`  

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.  

## Summary

Create a Claude Code skill that fetches Slack thread conversations via Slack MCP server and posts them as formatted markdown comments to JIRA tickets at https://jounce.atlassian.net/ (should be in .env file under JIRA_PROJECT_URL).  The skill will parse Slack URLs, extract thread messages, optionally generate AI summaries, and upload to JIRA using the existing upload pattern from `upload-chat-log` skill.  

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: Slack / JIRA MCP servers (MCP tools)  
**Storage**: Temporary file storage in `/tmp/claude/` directory  
**Testing**: pytest (contract, integration, unit tests)  
**Target Platform**: Claude Code CLI environment (macOS/Linux)  
**Project Type**: Single project (skill within claude-plugins structure)  
**Performance Goals**: Complete workflow in <30 seconds, handle up to 50 messages  
**Constraints**: <200ms for URL parsing, graceful handling of API rate limits  
**Scale/Scope**: Single skill, ~3-4 Python modules, reuse existing JIRA upload utilities  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*  

### Pre-Research Check

| Gate | Status | Notes |
|------|--------|-------|
| **Code Quality First** | ✓ PASS | Will use type hints, keep functions <10 complexity, enforce linting |
| **Test-Driven Development** | ✓ PASS | TDD workflow planned: contract → integration → unit tests |
| **UV Package Management** | ✓ PASS | Using PEP 723 inline script metadata with uv |
| **Python Standards** | ✓ PASS | No `__init__.py` files (implicit namespace), f-strings, type hints |
| **Library-First Architecture** | ✓ PASS | Skill as standalone library with CLI interface |
| **Testing Framework** | ✓ PASS | pytest only, flat functions, parametrize for variations |
| **File Size Limit** | ✓ PASS | Target ≤2048 tokens per file, split into modules |
| **Performance by Design** | ✓ PASS | Performance targets defined in spec (SC-001: 30s total) |
| **Observability** | ✓ PASS | stdin/stdout pattern, errors to stderr, structured logging |

**Result**: All gates PASS. No violations requiring justification.  

### Post-Design Check

*To be completed after Phase 1*  

## Project Structure

### Documentation (this feature)

```text
specs/001-jira-upload-slack-thread/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli-interface.md # CLI contract specification
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
claude-plugins/jira/skills/upload-slack-thread/
├── SKILL.md             # Skill metadata and usage documentation
└── scripts/
    ├── upload_slack_thread.py      # Main entry point (PEP 723 script)
    ├── slack_fetcher.py            # Slack MCP interaction module
    ├── url_parser.py               # URL parsing and validation
    ├── markdown_formatter.py       # Markdown generation
    ├── jira_comment_poster.py      # JIRA comment posting (reuse upload_chat_log pattern)
    └── ticket_extractor.py         # JIRA ticket key extraction from text

tests/
├── contract/
│   └── test_upload_slack_thread_contract.py
├── integration/
│   ├── test_slack_mcp_integration.py
│   └── test_jira_mcp_integration.py
└── unit/
    ├── test_url_parser.py
    ├── test_ticket_extractor.py
    ├── test_markdown_formatter.py
    ├── test_slack_fetcher.py
    └── test_jira_comment_poster.py
```

**Structure Decision**: Single project structure following existing `claude-plugins/jira/skills/` pattern. Skill will be standalone with multiple focused modules to maintain file size limits and single responsibility principle. Reuses existing JIRA authentication and upload patterns from `upload-chat-log` skill.  

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**  

No violations. All constitution checks pass.  

### Post-Design Check (Completed)

| Gate | Status | Notes |
|------|--------|-------|
| **Code Quality First** | ✓ PASS | Data model uses dataclasses with type hints, validation in `__post_init__` |
| **Test-Driven Development** | ✓ PASS | Contract tests defined, test structure established |
| **UV Package Management** | ✓ PASS | PEP 723 dependencies in script header |
| **Python Standards** | ✓ PASS | Dataclasses for entities, f-strings for formatting, no __init__.py |
| **Library-First Architecture** | ✓ PASS | Modular design: 6 focused modules, each with single responsibility |
| **Testing Framework** | ✓ PASS | pytest structure: contract/ integration/ unit/ directories |
| **File Size Limit** | ✓ PASS | Each module designed to stay under 2048 tokens |
| **Performance by Design** | ✓ PASS | Performance targets in CLI contract, measured per operation |
| **Observability** | ✓ PASS | CLI contract defines stdout/stderr separation, structured errors |

**Final Result**: All gates PASS. Design adheres to constitution. Ready for implementation (Phase 2: tasks.md generation via `/speckit.tasks` command).  

---  

## Phase 0: Research - COMPLETED ✓

See [research.md](./research.md) for complete findings.  

**Key Decisions**:  
1. Slack MCP Server for all Slack interactions  
2. JIRA comments (not attachments) via jira.add_comment()  
3. Regex pattern `[A-Z]+-\d+` for ticket extraction  
4. Truncate at 50 messages with warning  
5. Optional AI summary via `--summary` flag (default OFF)  

**All technical unknowns resolved. No blockers.**  

---  

## Phase 1: Design & Contracts - COMPLETED ✓

### Artifacts Created

1. **data-model.md**: Defines 8 core entities with validation rules  
   - SlackThreadURL, ThreadMessage, AttachmentMetadata  
   - SlackThread, JIRATicketKey, MarkdownExport, JIRAComment  
   - State transitions and relationships documented  

2. **contracts/cli-interface.md**: Complete CLI specification  
   - Command signature, arguments, flags  
   - Exit codes, output streams, error messages  
   - Performance contract, compatibility requirements  

3. **quickstart.md**: User-facing documentation  
   - Prerequisites, installation, usage examples  
   - Common use cases, troubleshooting guide  
   - Advanced usage patterns  

4. **Agent Context Updated**: CLAUDE.md includes Slack MCP patterns  

### Design Highlights

**Modular Architecture**:  
- 6 focused Python modules, each <2048 tokens  
- Clear separation: parsing, fetching, formatting, posting  
- Reuses existing JIRA upload patterns  

**Data Flow**:  
```text
URL → SlackThreadURL → SlackThread → MarkdownExport → JIRAComment → JIRA API
       (parse)          (fetch)        (format)        (post)
```

**Error Strategy**:  
- Fail fast with actionable messages  
- stdout for success, stderr for errors  
- Specific exit codes per error type  

**Test Coverage**:  
- Contract tests: CLI interface, I/O streams, exit codes  
- Integration tests: Slack MCP, JIRA API  
- Unit tests: Each module independently  

---  

## Phase 2: Tasks Generation - PENDING

**Next Command**: `/speckit.tasks`  

**What it will do**:  
1. Generate `tasks.md` with TDD-ordered implementation tasks  
2. Break down into: contract tests → integration tests → unit tests → implementation  
3. Prioritize by user story (P1 → P2 → P3)  
4. Include acceptance criteria for each task  

**Estimated Task Count**: 15-20 tasks  
**Estimated Implementation Time**: Not estimated (per plan guidelines)  

---  

## Summary

This implementation plan defines a complete Claude Code skill for uploading Slack threads to JIRA tickets.  

**Key Technical Decisions**:  
- Slack MCP server for API interaction (no direct SDK)  
- JIRA comments for inline visibility (not attachments)  
- Truncation at 50 messages for performance  
- Optional AI summary controlled by flag  

**Architecture**:  
- Single-project skill following existing patterns  
- 6 modular Python files with clear responsibilities  
- Full test coverage (contract, integration, unit)  
- PEP 723 inline dependencies via UV  

**Documentation**:  
- Complete data model with validation rules  
- Detailed CLI contract with examples  
- User-friendly quickstart guide  

**Constitution Compliance**:  
- All gates passed (pre and post design)  
- No violations or exceptions required  
- TDD workflow planned  
- UV for package management  
- pytest for testing  

**Status**: Ready for task generation (Phase 2)  

**Branch**: `001-jira-upload-slack-thread`  
**Spec**: [spec.md](./spec.md)  
**Research**: [research.md](./research.md)  
**Data Model**: [data-model.md](./data-model.md)  
**Contracts**: [contracts/cli-interface.md](./contracts/cli-interface.md)  
**Quickstart**: [quickstart.md](./quickstart.md)  

## Additional Implementation Notes

### Message Consolidation

**Requirement**: Consecutive messages from the same user must be merged into single blocks in the markdown output.  

**Impact**:  
- Enhances readability of exported threads  
- Reduces visual clutter in JIRA comments  
- Implementation in `markdown_formatter.py` module  

**Example**:  
Multiple consecutive messages from "John Doe" will appear as:  
```markdown
### John Doe - 2026-01-26 10:15
First message

Second message

Third message
```

Instead of three separate message blocks.  

### Configuration Changes

**JIRA URL Configuration**:  
- JIRA_PROJECT_URL must be loaded from .env file or environment  
- Not hardcoded to specific instance  
- Example: `JIRA_PROJECT_URL=https://jounce.atlassian.net/`  

**MCP Server Updates**:  
- Both Slack and JIRA interactions use MCP servers  
- No direct Python library dependencies (slack-sdk, jira)  
- Consistent MCP tool pattern across both services  
