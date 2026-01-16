# Agor Templates for Speckit Workflow

Ready-to-use Agor templates for each stage of the Speckit workflow. Copy these directly into your Agor board.

> **Main Guide**: See [agor-speckit-workflow.md](agor-speckit-workflow.md) for full workflow documentation.

## Template Overview

| Stage | Behavior | Template |
|-------|----------|----------|
| [1. Setup](#stage-1-setup) | `always_new` | Initialize project, link Jira, create PR |
| [2. Specify](#stage-2-specify) | `always_new` | Create specification from Jira context |
| [3. Clarify](#stage-3-clarify) | `show_picker` | Resolve ambiguities before planning |
| [4. Plan](#stage-4-plan) | `show_picker` | Create technical implementation plan |
| [5. Tasks](#stage-5-tasks) | `show_picker` | Generate actionable task list |
| [6. Analyze](#stage-6-analyze) | `show_picker` | Cross-artifact consistency check |
| [7. Implement](#stage-7-implement) | `show_picker` | Execute implementation tasks |

---

## Stage 1: Setup

**Behavior**: `always_new`

```
DO NOT RUN: `just p` in this session!

- Copy /Users/yourname/projects/spec-kit/CLAUDE.md to CLAUDE.md
- Run uv sync
- Run: y | specify init . --ai claude --script sh
- Copy constitution from /Users/yourname/.config/specify/constitution.md
  to .specify/memory/constitution.md
- Replace common.sh file with /Users/yourname/projects/spec-kit/scripts/bash/common.sh
- Update pyproject.toml [tool.lintok] to exclude "specs/**"

Jira Integration:
- If {worktree.issue_url} is null, get Jira issue based on Git branch name
  - Update {worktree.issue_url} with https://jounce.atlassian.net/browse/JN-XXXX
  - Branch format: jn-3767-post-processing-db → issue JN-3767

- If branch name > 55 characters, suggest shortening (keep Jira prefix)

- If {worktree.pull_request_url} is empty:
  - Check for existing PR with Jira ticket reference
  - Create DRAFT PR if none exists
```

### Customization Notes

- Replace `/Users/yourname/projects/spec-kit/` with your team's spec-kit location
- Replace `jounce.atlassian.net` with your Jira instance
- Replace `JN-` with your project's ticket prefix

---

## Stage 2: Specify

**Behavior**: `always_new`

```
Create the spec document. Focus on the what and why, not the tech stack.

- Pipe the content of {worktree.issue_url} into /speckit.specify

If {worktree.issue_url} is a Jira subtask, get additional background
from the parent story if necessary.
```

### Manual Execution

```bash
# Basic specification
specify spec

# Or with Claude Code skill
/speckit.specify
```

---

## Stage 3: Clarify

**Behavior**: `show_picker`

```
If git is dirty, stage all files and commit with:
git commit -m "wip: pre-clarify cleanup" --no-verify

Run /speckit.clarify

Or: .specify/scripts/bash/check-prerequisites.sh --json --paths-only
```

### What Gets Clarified

- Ambiguous acceptance criteria
- Missing edge case definitions
- Unclear business rules
- Integration requirements
- Performance expectations

---

## Stage 4: Plan

**Behavior**: `show_picker`

```
If git is dirty, run:
git add . && git commit -m "wip: pre-plan cleanup"

Create a technical implementation plan.
Run /speckit.plan
```

### Best Practices

- Always commit WIP changes before planning
- Reference the spec in your plan
- Include test strategy
- Note areas of uncertainty

---

## Stage 5: Tasks

**Behavior**: `show_picker`

```
Run /speckit.tasks
```

### Task Quality Checklist

Good tasks are:

- **Atomic**: Completable in one focused session
- **Testable**: Have clear completion criteria
- **Independent**: Minimize dependencies on other tasks
- **Sized appropriately**: Not too large, not too granular

---

## Stage 6: Analyze

**Behavior**: `show_picker`

```
Run /speckit.analyze
```

### What Gets Analyzed

- Consistency across spec, plan, and tasks
- Coverage gaps
- Potential conflicts
- Implementation readiness

---

## Stage 7: Implement

**Behavior**: `show_picker`

```
Run /speckit.implement
```

### Implementation Guidelines

1. **Follow the plan**: Stick to the technical design
2. **One task at a time**: Complete tasks sequentially or parallelize with Agor
3. **Test continuously**: Write tests alongside implementation
4. **Commit frequently**: Small, atomic commits with clear messages

---

## Session Behavior Reference

### `always_new`

- Creates a fresh session every time
- No prior context carried over
- Use for: Setup, Specify (stages that need clean starts)

### `show_picker`

- Prompts to choose existing or new session
- Allows reusing context from previous work
- Use for: Clarify, Plan, Tasks, Analyze, Implement (stages that may iterate)

---

## Template Variables

These variables are available in Agor templates:

| Variable | Description |
|----------|-------------|
| `{worktree.issue_url}` | Jira ticket URL linked to the worktree |
| `{worktree.pull_request_url}` | PR URL linked to the worktree |
| `{worktree.branch}` | Current Git branch name |

---

## Quick Copy Reference

### All Templates (Compact)

```
# Stage 1: Setup (always_new)
Initialize speckit, link Jira {worktree.issue_url}, create draft PR

# Stage 2: Specify (always_new)
Pipe {worktree.issue_url} into /speckit.specify

# Stage 3: Clarify (show_picker)
Commit WIP, run /speckit.clarify

# Stage 4: Plan (show_picker)
Commit WIP, run /speckit.plan

# Stage 5: Tasks (show_picker)
Run /speckit.tasks

# Stage 6: Analyze (show_picker)
Run /speckit.analyze

# Stage 7: Implement (show_picker)
Run /speckit.implement
```
