# AutoClaude Spec Schemas

Reference schemas for AutoClaude spec files.

## Directory Structure

```
.auto-claude/
├── specs/
│   └── XXX-task-name/
│       ├── spec.md
│       ├── requirements.json
│       ├── context.json
│       ├── implementation_plan.json
│       ├── qa_report.md (generated after QA)
│       └── QA_FIX_REQUEST.md (generated if QA fails)
└── TASKS.md (optional - source file)
```

## spec.md

The human-readable specification document:

```markdown
# Task Title

## Overview
Brief description of what this task accomplishes.

## Requirements
- Requirement 1
- Requirement 2

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Approach
Description of implementation approach.

## Dependencies
- TASK-XXX: Dependency description

## Notes
Additional context and considerations.
```

## requirements.json

```json
{
  "task_id": "001",
  "task_name": "task-name-slug",
  "title": "Human Readable Title",
  "description": "Full description of the task",
  "area": "Component/Feature area",
  "status": "pending|in_progress|completed|blocked",
  "priority": "p0|p1|p2|p3",
  "complexity": "simple|standard|complex",
  "dependencies": ["001", "002"],
  "acceptance_criteria": [
    "Criterion 1",
    "Criterion 2"
  ],
  "notes": "Additional context",
  "created_at": "2025-01-30T00:00:00Z",
  "updated_at": "2025-01-30T00:00:00Z",
  "completed_at": null
}
```

## context.json

Discovered codebase context (populated by AutoClaude agents):

```json
{
  "project_type": "react|python|node|...",
  "relevant_files": [
    {
      "path": "src/components/Example.tsx",
      "relevance": "Contains related component",
      "patterns": ["hooks", "state management"]
    }
  ],
  "dependencies": {
    "runtime": ["react", "typescript"],
    "dev": ["jest", "eslint"]
  },
  "patterns_discovered": [
    "Uses React hooks for state",
    "Follows atomic design principles"
  ],
  "related_specs": ["001", "003"]
}
```

## implementation_plan.json

Subtask-based plan with status tracking:

```json
{
  "spec_id": "001",
  "spec_name": "task-name-slug",
  "complexity": "standard",
  "total_chunks": 3,
  "completed_chunks": 0,
  "status": "pending|in_progress|completed|qa_review|qa_fix",
  "chunks": [
    {
      "id": 1,
      "title": "Subtask 1",
      "description": "What this subtask accomplishes",
      "status": "pending|in_progress|completed",
      "files_to_modify": ["src/file1.ts"],
      "files_to_create": ["src/file2.ts"],
      "acceptance_criteria": ["Criterion 1"],
      "dependencies": [],
      "session_count": 0,
      "last_session": null
    },
    {
      "id": 2,
      "title": "Subtask 2",
      "description": "What this subtask accomplishes",
      "status": "pending",
      "files_to_modify": [],
      "files_to_create": ["tests/file1.test.ts"],
      "acceptance_criteria": ["Tests pass"],
      "dependencies": [1],
      "session_count": 0,
      "last_session": null
    }
  ],
  "created_at": "2025-01-30T00:00:00Z",
  "updated_at": "2025-01-30T00:00:00Z"
}
```

## Status Values

### Task Status
- `pending` - Not started
- `in_progress` - Currently being worked on
- `completed` - All acceptance criteria met
- `blocked` - Waiting on dependencies or external factors

### Chunk Status
- `pending` - Not started
- `in_progress` - Agent currently working
- `completed` - Chunk finished and verified

### Plan Status
- `pending` - Plan created, not started
- `in_progress` - Implementation underway
- `qa_review` - QA agent reviewing
- `qa_fix` - Fixing QA-identified issues
- `completed` - All chunks done, QA passed

## Control Files

Optional files for human-in-the-loop control:

### PAUSE
Create empty file to pause after current session:
```bash
touch .auto-claude/specs/001-task-name/PAUSE
```

### HUMAN_INPUT.md
Provide guidance to the agent:
```markdown
Focus on fixing the login bug first.
Use the existing auth helper instead of creating a new one.
```
