# Tasks: JIRA Upload Slack Thread

**Input**: Design documents from `/specs/001-jira-upload-slack-thread/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md

**Tests**: Tests are included per TDD workflow specified in plan.md and CLAUDE.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md project structure:
- **Skill**: `claude-plugins/jira/skills/upload-slack-thread/`
- **Scripts**: `claude-plugins/jira/skills/upload-slack-thread/scripts/`
- **Tests**: `tests/contract/`, `tests/integration/`, `tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Verify Slack MCP server and JIRA MCP server are configured and accessible
- [X] T002 Create skill directory structure per plan.md at claude-plugins/jira/skills/upload-slack-thread/
- [X] T003 [P] Create SKILL.md with YAML frontmatter (name, description, argument-hint) and usage instructions at claude-plugins/jira/skills/upload-slack-thread/SKILL.md
- [X] T004 [P] Create main entry point with PEP 723 metadata at claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py
- [X] T005 Create test directory structure per plan.md at tests/contract/, tests/integration/, tests/unit/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement SlackThreadURL dataclass with validation in claude-plugins/jira/skills/upload-slack-thread/scripts/url_parser.py
- [X] T007 [P] Implement JIRATicketKey dataclass with validation in claude-plugins/jira/skills/upload-slack-thread/scripts/ticket_extractor.py
- [X] T008 [P] Implement ThreadMessage and AttachmentMetadata dataclasses in claude-plugins/jira/skills/upload-slack-thread/scripts/slack_fetcher.py
- [X] T009 [P] Implement SlackThread dataclass with truncation logic in claude-plugins/jira/skills/upload-slack-thread/scripts/slack_fetcher.py
- [X] T010 Implement CLI argument parsing with argparse in claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py
- [X] T011 [P] Implement error handling utilities with exit codes per cli-interface.md in claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py
- [X] T012 [P] Implement environment variable loading (JIRA_API_TOKEN, JIRA_PROJECT_URL) in claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Export Slack Thread to JIRA Ticket (Priority: P1) MVP

**Goal**: A team member can export a Slack thread conversation to a JIRA ticket as a formatted markdown comment

**Independent Test**: Provide a Slack thread URL and JIRA ticket key, verify markdown content appears as comment on ticket with correctly formatted content

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for CLI argument validation in tests/contract/test_upload_slack_thread_contract.py
- [X] T014 [P] [US1] Contract test for exit codes and output streams in tests/contract/test_upload_slack_thread_contract.py
- [X] T015 [P] [US1] Unit test for URL parsing in tests/unit/test_url_parser.py
- [X] T016 [P] [US1] Unit test for ticket extraction from text in tests/unit/test_ticket_extractor.py
- [X] T017 [P] [US1] Unit test for markdown formatting in tests/unit/test_markdown_formatter.py
- [X] T018 [P] [US1] Unit test for Slack fetcher (mock MCP) in tests/unit/test_slack_fetcher.py
- [X] T019 [P] [US1] Unit test for JIRA comment poster in tests/unit/test_jira_comment_poster.py
- [X] T020 [P] [US1] Integration test for Slack MCP interaction in tests/integration/test_slack_mcp_integration.py
- [X] T021 [P] [US1] Integration test for JIRA MCP server interaction in tests/integration/test_jira_mcp_integration.py

### Implementation for User Story 1

- [X] T022 [US1] Implement parse_slack_url() function in claude-plugins/jira/skills/upload-slack-thread/scripts/url_parser.py
- [X] T023 [US1] Implement extract_ticket_from_text() function in claude-plugins/jira/skills/upload-slack-thread/scripts/ticket_extractor.py
- [X] T024 [US1] ~~Implement fetch_thread_messages() via Slack MCP~~ **N/A - Claude calls mcp__slack__conversations_replies directly per SKILL.md**
- [X] T025 [US1] ~~Implement resolve_user_names() via Slack MCP~~ **N/A - Claude resolves from MCP response per SKILL.md**
- [X] T026 [US1] Implement merge_consecutive_messages() in claude-plugins/jira/skills/upload-slack-thread/scripts/markdown_formatter.py
- [X] T027 [US1] Implement MarkdownExport dataclass in claude-plugins/jira/skills/upload-slack-thread/scripts/markdown_formatter.py
- [X] T028 [US1] Implement format_thread_to_markdown() in claude-plugins/jira/skills/upload-slack-thread/scripts/markdown_formatter.py
- [X] T029 [US1] Implement JIRAComment dataclass in claude-plugins/jira/skills/upload-slack-thread/scripts/jira_comment_poster.py
- [X] T030 [US1] ~~Implement post_comment_to_jira() via JIRA MCP~~ **N/A - Claude calls mcp__mcp-atlassian__jira_add_comment directly per SKILL.md**
- [X] T031 [US1] ~~Implement main workflow orchestration~~ **N/A - Claude orchestrates workflow via SKILL.md instructions**
- [X] T032 [US1] ~~Implement user prompting for missing ticket key~~ **N/A - SKILL.md instructs Claude to ask user**
- [X] T033 [US1] ~~Add verbose logging (--verbose flag)~~ **N/A - Claude handles logging**

**Checkpoint**: User Story 1 fully functional - can export Slack thread to JIRA comment

**Architecture Note**: This is a Claude Code skill. Claude executes SKILL.md instructions directly using MCP tools. Python scripts provide data models and formatting utilities only.

---

## Phase 4: User Story 3 - Handle Primary Slack Thread Format (Priority: P1)

**Goal**: User provides a direct Slack thread URL and the system correctly parses it

**Independent Test**: Provide a direct thread URL format and verify it parses correctly

**Scope**: MVP handles only direct thread link format: `https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP`

**Deferred to later stages**:
- thread_ts query parameter format (`?thread_ts=...`)
- Other URL variations

### Tests for User Story 3

- [X] T034 [P] [US3] Unit test for malformed URL error messages in tests/unit/test_url_parser.py

### Implementation for User Story 3

- [X] T035 [US3] Add clear error messages for malformed URLs per cli-interface.md in claude-plugins/jira/skills/upload-slack-thread/scripts/url_parser.py

**Checkpoint**: Primary Slack URL format handled correctly with clear errors for invalid URLs

**Note**: url_parser.py already includes SlackURLParseError with descriptive messages.

---

## Phase 5: User Story 2 - Optional Thread Summary Generation (Priority: P2)

**Goal**: A team member can optionally generate an AI summary of a Slack thread to quickly understand key points

**Independent Test**: Provide a multi-message Slack thread with --summary flag and verify markdown includes a concise summary section at the top

### Tests for User Story 2

- [X] T036 [P] [US2] Contract test for --summary flag behavior in tests/contract/test_upload_slack_thread_contract.py
- [X] T037 [P] [US2] ~~Unit test for summary generation~~ **N/A - Claude generates summary per SKILL.md**

### Implementation for User Story 2

- [X] T038 [US2] ~~Implement generate_thread_summary()~~ **N/A - Claude generates summary inline per SKILL.md Step 5**
- [X] T039 [US2] Integrate summary into MarkdownExport.full_content in claude-plugins/jira/skills/upload-slack-thread/scripts/markdown_formatter.py
- [X] T040 [US2] Add --summary/-s flag to CLI in claude-plugins/jira/skills/upload-slack-thread/scripts/upload_slack_thread.py
- [X] T041 [US2] ~~Handle summary generation failure gracefully~~ **N/A - Claude handles this per SKILL.md**

**Checkpoint**: AI summary generation works when requested

**Note**: SKILL.md Step 5 instructs Claude to generate "AI-generated 1-2 paragraph summary" when --summary flag is provided. MarkdownExport.summary field is ready to accept it.

### Implementation for User Story 2a (--summary-only flag)

- [X] T050 [P] [US2] Add --summary-only parameter documentation to SKILL.md synopsis and parameters
- [X] T051 [P] [US2] Update Step 5 formatting logic in SKILL.md for --summary-only output format
- [X] T052 [P] [US2] Update skill README.md with --summary-only usage example
- [X] T053 [P] [US2] Update claude-plugins/jira/README.md with --summary-only parameter
- [X] T054 [P] [US2] Update spec.md with --summary-only acceptance scenarios (US2 scenarios 4-5) and FR-012a

**Checkpoint**: --summary-only flag documented and ready for use

---

## Phase 6: User Story 4 - Search Conversation Context for JIRA Ticket (Priority: P3)

**Goal**: When a user doesn't provide a JIRA ticket key, the system searches the Slack thread for ticket references

**Independent Test**: Provide a Slack thread URL without ticket key where thread contains ticket reference, verify auto-detection

### Tests for User Story 4

- [X] T042 [P] [US4] Unit test for ticket extraction from thread messages in tests/unit/test_ticket_extractor.py
- [X] T043 [P] [US4] Unit test for first-occurrence chronological order in tests/unit/test_ticket_extractor.py

### Implementation for User Story 4

- [X] T044 [US4] Implement extract_ticket_from_text() in claude-plugins/jira/skills/upload-slack-thread/scripts/ticket_extractor.py
- [X] T045 [US4] ~~Integrate auto-detection into main workflow~~ **N/A - SKILL.md Step 4 instructs Claude to search thread messages for ticket pattern**

**Checkpoint**: Ticket auto-detection from thread content works

**Note**: SKILL.md Step 4 instructs Claude: "Search all message text for JIRA ticket pattern `[A-Z]+-\d+`, use first match found (chronological order)". extract_ticket_from_text() provides the regex utility.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Complete SKILL.md with full implementation steps, examples, and error handling per Claude Code skill docs at claude-plugins/jira/skills/upload-slack-thread/SKILL.md
- [ ] T047 Verify all tests pass with pytest in tests/
- [ ] T048 Run pre-commit checks (just p) across all new files
- [ ] T049 Run quickstart.md validation scenarios manually

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (Phase 3) and US3 (Phase 4) are both P1 priority
  - US1 contains core functionality, US3 extends URL parsing
  - US2 (Phase 5) and US4 (Phase 6) can proceed after US1
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Core MVP functionality
- **User Story 3 (P1)**: Can start after Foundational - URL format variations (can parallel with US1 after T021)
- **User Story 2 (P2)**: Depends on US1 T027 (markdown formatter) - Adds summary generation
- **User Story 4 (P3)**: Depends on US1 T022 (ticket extraction) - Extends auto-detection

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Dataclasses before functions
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks T005-T011 marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- US1 and US3 can be worked on in parallel after Phase 2 completes

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for CLI argument validation in tests/contract/test_upload_slack_thread_contract.py"
Task: "Contract test for exit codes and output streams in tests/contract/test_upload_slack_thread_contract.py"
Task: "Unit test for URL parsing in tests/unit/test_url_parser.py"
Task: "Unit test for ticket extraction in tests/unit/test_ticket_extractor.py"
Task: "Unit test for markdown formatting in tests/unit/test_markdown_formatter.py"
Task: "Unit test for Slack fetcher in tests/unit/test_slack_fetcher.py"
Task: "Unit test for JIRA comment poster in tests/unit/test_jira_comment_poster.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 3)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T012)
3. Complete Phase 3: User Story 1 (T013-T033)
4. Complete Phase 4: User Story 3 (T034-T035)
5. **STOP and VALIDATE**: Test core export workflow independently
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!)
3. Add User Story 3 -> Test primary URL format + error handling -> Deploy/Demo
4. Add User Story 2 -> Test AI summary -> Deploy/Demo
5. Add User Story 4 -> Test auto-detection -> Deploy/Demo
6. Each story adds value without breaking previous stories

---

## Task Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 5 |
| Phase 2 | Foundational | 7 |
| Phase 3 | User Story 1 (P1) - Core Export | 21 |
| Phase 4 | User Story 3 (P1) - Primary URL Format | 2 |
| Phase 5 | User Story 2 (P2) - AI Summary | 6 |
| Phase 5a | User Story 2a - --summary-only flag | 5 |
| Phase 6 | User Story 4 (P3) - Auto-Detection | 4 |
| Phase 7 | Polish | 4 |
| **Total** | | **54** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All Slack AND JIRA interactions use MCP servers (no direct Python SDK libraries)
- Temporary files stored in /tmp/claude/ directory
