---
name: autoclaude-task-converter
description: Convert single-file task backlogs (TASKS.md format) to AutoClaude multi-file spec structure. Use when the user wants to (1) convert existing TASKS.md or similar task backlog files to AutoClaude specs, (2) initialize a new project with AutoClaude-compatible task structure, (3) migrate task definitions from simple markdown to the multi-file spec format with requirements.json, context.json, implementation_plan.json. Triggers on phrases like "convert tasks to AutoClaude", "set up AutoClaude specs", "migrate backlog", "create spec from task".
---

# AutoClaude Task Converter

Convert markdown task backlogs to AutoClaude's multi-file spec structure.

## Input Format

The skill accepts task files in this markdown format:

```markdown
### TASK-XXX: Task Title
- **Description**: What needs to be done
- **Area**: Component/Feature area
- **Status**: To Do | In Progress | Done | Blocked
- **Priority**: Critical | High | Medium | Low
- **Dependencies**: TASK-XXX, TASK-YYY (optional)
- **Subtasks**: (optional)
  - [ ] Subtask 1
  - [x] Subtask 2 (completed)
- **Notes**: Additional context
```

Also supports single-line tasks: `- [ ] Simple task description`

## Output Structure

For each task, create `.auto-claude/specs/XXX-task-name/` containing:

| File | Purpose |
|------|---------|
| `spec.md` | Feature specification |
| `requirements.json` | Structured requirements |
| `context.json` | Codebase context (initially empty) |
| `implementation_plan.json` | Subtasks with status |

## Workflow

### Converting Existing Tasks

1. **Locate task file**: Find TASKS.md, TODO.md, or similar in project root
2. **Parse tasks**: Extract structured data from markdown
3. **Create spec directories**: Run `scripts/convert_tasks.py`
4. **Verify output**: Check `.auto-claude/specs/` structure

```bash
python3 scripts/convert_tasks.py --input TASKS.md --output .auto-claude/specs
```

### New Project Setup

When no task file exists, create the AutoClaude structure:

```bash
python3 scripts/convert_tasks.py --init --output .auto-claude/specs
```

This creates:
- `.auto-claude/specs/` directory
- `.auto-claude/TASKS.md` template file
- Sample spec `001-project-setup/`

## Conversion Rules

### Status Mapping

| Input Status | AutoClaude Status |
|--------------|-------------------|
| `To Do` | `pending` |
| `In Progress` | `in_progress` |
| `Done` | `completed` |
| `Blocked` | `blocked` |

### Priority Mapping

| Input Priority | AutoClaude Priority |
|----------------|---------------------|
| `Critical` | `p0` |
| `High` | `p1` |
| `Medium` | `p2` |
| `Low` | `p3` |

### Complexity Assessment

Determined by subtask count and description length:
- **simple**: 0-2 subtasks, single area
- **standard**: 3-6 subtasks, may span areas
- **complex**: 7+ subtasks, multiple dependencies

## File Schemas

See `references/autoclaude_schemas.md` for detailed JSON schemas for:
- `requirements.json`
- `context.json`
- `implementation_plan.json`

## Post-Conversion Note

**IMPORTANT**: After writing task specs, always inform the user:

```
NOTE: CURRENTLY AUTOCLAUDE MAY REQUIRE A RESTART BEFORE FULLY UTILIZING TASKS THAT HAVE BEEN WRITTEN OUT.
```
