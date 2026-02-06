---
description: Create a git commit following AIPCC conventions
argument-hint: [JIRA-TICKET]
---

## Name
odh-ai-helpers:aipcc-commit

## Synopsis
```
/aipcc:commit           # Create commit, infer JIRA ticket from branch/changes
/aipcc:commit AIPCC-123 # Create commit with specified JIRA ticket
```

## Description
Creates a single git commit following the AIPCC (AI Platform Continuous Compliance) commit message format. This format is required for Red Hat AI projects using GitLab's JIRA ticket linter.

**Key features:**
- Automatically stages changes and creates commits
- Validates commit message format before finalizing
- Ensures DCO compliance with `--signoff`
- Supports JIRA ticket inference from branch name

## Implementation

### Context Gathering
First, gather the current repository state:
- Run `git status` to see staged/unstaged changes
- Run `git diff HEAD` to see all changes
- Run `git branch --show-current` to get current branch
- Run `git log --oneline -5` to see recent commit style

### Commit Message Format

The commit message MUST follow this exact format:

```
<JIRA-TICKET>: <Short description>

<Longer description explaining what changed and why>

Co-authored-by: <model>@<version> (claude code)
Signed-off-by: <Author Name> <email>
```

**Requirements:**
1. **Title line**: Must start with a JIRA ticket ID matching: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX:`
2. **Body**: Must include at least one line of description after an empty line
3. **Co-authored-by**: When AI assisted, include `Co-authored-by: <model>@<version> (claude code)`
4. **Signed-off-by**: Must include a `Signed-off-by:` line (use `--signoff` flag)

### Execution Steps

1. Stage files with `git add`
2. Create the commit using `git commit --signoff -m "$(cat <<'EOF'
<commit message here>
EOF
)"`
3. Validate the commit message meets all requirements
4. If validation fails, fix with `git commit --amend --signoff` and re-validate

### Validation Rules

After creating the commit, verify:
- [ ] Subject starts with valid JIRA prefix
- [ ] Blank line between subject and body
- [ ] Body contains at least one descriptive sentence
- [ ] `Signed-off-by:` line present with valid format

## Examples

### Basic commit with inferred ticket
```bash
# On branch AIPCC-1234-add-validation
git add src/validator.ts
/aipcc:commit
```
Creates:
```
AIPCC-1234: Add input validation for user forms

Implement validation rules to prevent invalid data from being
submitted through the user registration form.

Co-authored-by: claude-sonnet-4@20250514 (claude code)
Signed-off-by: Jane Developer <jane@redhat.com>
```

### Commit with explicit ticket
```bash
/aipcc:commit INFERENG-5678
```

## Arguments

- **[JIRA-TICKET]** (optional): JIRA ticket ID to use in commit message
  - If omitted: Inferred from branch name (e.g., `AIPCC-1234-feature` → `AIPCC-1234`)
  - Format: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX`

## See Also
- **`/aipcc:commit-suggest`** – Generate commit message suggestions without committing
- **`/aipcc:commit-push-pr`** – Create commit, push, and open a PR in one command
- **`/aipcc:fix-pr-commit`** – Fix non-compliant commits on existing PRs
- **`aipcc-commit-validator`** skill – Validate commits with the standalone script
