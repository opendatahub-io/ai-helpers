---
name: aipcc-commit-validator
description: Validate git commit messages against AIPCC linter rules used by Red Hat AI projects. Checks for proper JIRA ticket format, commit body, and Signed-off-by line. Use this when validating commits before pushing or when CI fails due to commit message format.
allowed-tools: Bash Read
---

# AIPCC Commit Validator

This skill validates git commit messages against the AIPCC (AI Platform Continuous Compliance) linter rules used by Red Hat AI projects. It mimics the JIRA ticket linter used in GitLab CI.

## Validation Rules

The validator checks three rules:

1. **JIRA Ticket Prefix**: Subject must start with a valid JIRA ticket ID
   - Pattern: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX:`
   - Example: `AIPCC-1234: Add new feature`

2. **Commit Body**: Must have a description after a blank line
   - The body should explain what changed and why

3. **Signed-off-by**: Must include DCO sign-off
   - Format: `Signed-off-by: Name <email@domain>`
   - Use `git commit --signoff` to add automatically

## Recommended Format

When AI assists with code changes, include the Co-authored-by line:

```
AIPCC-1234: Onboard package foobar

This commit onboards the foobar package needed by the foo team.

Co-authored-by: claude-sonnet-4@20250514 (claude code)
Signed-off-by: Your Name <your.email@example.com>
```

## Prerequisites

- Git repository
- Python 3.10+ with `uv` installed (script is self-contained)

## Instructions

**IMPORTANT**: Run the script from the user's git repository directory, not from the skill directory. Use the base directory (`<base_path>`) for this skill to execute the script with an absolute path.

### Validate Last Commit

```bash
uv run <base_path>/scripts/validate_commit.py
```

### Validate Specific Commit

```bash
uv run <base_path>/scripts/validate_commit.py abc1234
```

### Validate Range of Commits

```bash
# All commits on current branch vs main
uv run <base_path>/scripts/validate_commit.py origin/main..HEAD

# Last 3 commits
uv run <base_path>/scripts/validate_commit.py HEAD~3..HEAD
```

### Validate Multiple Specific Commits

```bash
uv run <base_path>/scripts/validate_commit.py abc1234 def5678 ghi9012
```

## Example Output

**Success:**
```
✓ All 3 commit(s) pass AIPCC linter validation
```

**Failure:**
```
✗ Commit validation failed:

  [abc1234] Subject must start with JIRA ticket (RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX:
    Got: fix typo in readme...

  [abc1234] Commit must have a body (description after blank line)

  [abc1234] Commit must include 'Signed-off-by: Name <email@domain>'
    Use: git commit --signoff
```

## Fixing Invalid Commits

If validation fails, fix with:

```bash
# Amend the last commit
git commit --amend --signoff

# Interactive rebase for multiple commits
git rebase -i origin/main
# Change 'pick' to 'reword' for commits to fix
```

## Related Commands

- `/aipcc:commit` - Create AIPCC-compliant commits
- `/aipcc:commit-push-pr` - Full commit, push, and PR workflow
- `/aipcc:fix-pr-commit` - Fix non-compliant PR commits by squashing
