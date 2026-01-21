---
description: "Create commit with automatic style detection based on development phase"
argument-hint: "[style_or_message]"
---

## Name
git:commit

## Synopsis
```
/git:commit [style_or_message]
```

## Description

Creates commits with appropriate verbosity based on development phase detection or explicit style arguments. Automatically stages all changes and generates intelligent commit messages.

## Usage
- `/git:commit` - Auto-detect style from context and create appropriate commit
- `/git:commit "Custom message"` - Use provided message as base, auto-detect style
- `/git:commit dev` - Force verbose development-style commit
- `/git:commit final` - Force concise final-style commit

## Style Detection

### Automatic Detection
The AI analyzes context clues to determine appropriate commit style:
- **Concise final style**: When changes represent completed features, bug fixes, or release-ready code
- **Verbose development style**: When changes are experimental, work-in-progress, or need detailed context

### Explicit Style Arguments
- **Verbose triggers**: `dev`, `wip`, `test`, `.` (any single character)
- **Concise triggers**: `fin`, `final`, `prod`, `done`, `complete`

## Implementation

### 1. Stage All Changes
```bash
git add -A
```

### 2. Generate Detailed Commit Message
The AI will analyze:
- All staged changes using `git diff --cached`
- Current git status and untracked files
- Recent commit context for consistency
- File modifications and their relationships

### 3. Generate Commit Message

#### Verbose Development Style
```
Brief summary of main change

Detailed context:
- Key architectural decisions made
- Files modified and why
- Any blockers encountered and solutions
- Dependencies or prerequisites
- Testing approach taken
- Next steps or follow-up needed

Co-authored-by: Claude <noreply@anthropic.com>
```

#### Concise Final Style
```
Brief summary of main change

- Key change 1
- Key change 2

Co-authored-by: Claude <noreply@anthropic.com>
```

## Style Selection Logic

### Context Analysis
The AI examines:
- **Change scope**: Small fixes vs large features
- **File types**: Documentation vs core functionality
- **Git history**: Pattern of recent commits
- **User language**: Words like "final", "ready", "WIP", "experiment"

### Override Rules
1. **Explicit style argument**: Always takes precedence
2. **User message content**: Detailed user message suggests verbose style
3. **Auto-detection**: Falls back to context analysis
4. **Default**: Verbose development style when uncertain

## Examples

1. **Auto-detect style**:
   ```
   /git:commit
   ```
   Claude analyzes context and chooses appropriate verbosity.

2. **Development checkpoint**:
   ```
   /git:commit dev
   ```
   Creates verbose commit preserving implementation context.

3. **Final commit**:
   ```
   /git:commit final
   ```
   Creates clean, concise commit suitable for main branch.

4. **Custom message with style**:
   ```
   /git:commit "Fix authentication bug"
   ```
   Uses provided message, auto-detects style for additional context.
