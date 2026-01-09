# Task Starter Command

You are helping the user start a new task with proper branch and folder tracking.

## Usage

`/task-starter <task-name>`

The task name will be provided as an argument to this command.

## Execution Steps

When this command is invoked, execute these steps in order:

1. **Extract task name** from the user's message
3. **Create new branch** with `git checkout -b <task-name>`
4. **Create task folder** with `mkdir -p branch-track/<task-name>`
5. **Create PLAN.md** in `branch-track/<task-name>/RPLAN.md` with task details
6. **Create upstream** with `git push -u origin <task-name>`

## PLAN Template

When creating the PLAN.md file in the task folder, use this template:

```markdown
# Task: <task-name>

**Created**: <current-date>
**Base Branch**: <base-branch>
**Status**: In Progress

## Description
<!-- Add task description here -->

## Progress
- [ ] Initial setup complete

## Notes
<!-- Add any relevant notes -->
```

## Output to User

After completing all steps, provide this summary:

```
✅ Task Started: <task-name>

📁 Created:
   - Branch: <task-name> (from <base-branch>)
   - Folder: branch-track/<task-name>/
   - Tracking: PLAN.md created

🔄 Ready to work on your task!
```

## Important Notes

- Always create the branch from t
he CURRENT working branch
- Ensure branch-track directory exists before creating task folder
- Use kebab-case for task names (lowercase with hyphens)
- Do NOT push to remote unless user explicitly requests it
- Handle errors gracefully if branch already exists
