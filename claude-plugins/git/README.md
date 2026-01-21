# Git Plugin

Git workflow automation and utilities for Claude Code.

## Commands

### `git:commit`

Create commits with automatic style detection based on development phase.

```
/git:commit [style_or_message]
```

- **Auto-detect style**: `/git:commit` - analyzes context to choose verbosity
- **Development checkpoint**: `/git:commit dev` - verbose commit with full context
- **Final commit**: `/git:commit final` - clean, concise commit message
- **Custom message**: `/git:commit "Fix authentication bug"`

### `git:merge`

Smart commit squashing with intelligent message combination.

```
/git:merge [count_or_sha] [style]
```

- **Merge last 2**: `/git:merge` or `/git:merge 1`
- **Merge N+1 commits**: `/git:merge 3` - merges HEAD + 3 previous
- **Merge to SHA**: `/git:merge abc1234` - merges from HEAD to SHA (inclusive)
- **With style**: `/git:merge 3 final` - squash with clean message

### `git:reword`

Smart commit message rewording with style transformation.

```
/git:reword [sha] [style_or_message]
```

- **Transform to verbose**: `/git:reword abc1234 dev`
- **Transform to concise**: `/git:reword abc1234 final`
- **Custom message**: `/git:reword abc1234 "New message"`
- **Auto-detect**: `/git:reword abc1234` - AI improves message

## Skills

### `shallow-clone`

Perform a shallow clone of a Git repository to a temporary location.

### `workflow`

Proactive git workflow automation that:
- **Detects substantial changes** and offers to create feature branches
- **Checkpoint commits** during development to save progress
- **Completion detection** recognizes when work is done
- **History cleanup** offers to squash and clean commit messages

The workflow skill orchestrates the commit, merge, and reword commands automatically during development sessions.

## Installation

```bash
/plugin install git@odh-ai-helpers
```

## Workflow Example

```
User: "I need to add OAuth authentication"

Claude: "Would you like me to create a feature branch?"
User: "Yes"

[During development]
Claude: "OAuth setup complete. Checkpoint commit?"
User: "Sure"
→ /git:commit dev

[After completion]
Claude: "We have 4 dev commits. Clean up before merging?"
User: "Yes, one commit"
→ /git:merge 3 final
```
