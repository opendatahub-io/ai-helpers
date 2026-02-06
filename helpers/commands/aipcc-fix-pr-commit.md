---
description: Fix non-compliant PR commits by squashing and recommitting
argument-hint: [JIRA-TICKET]
---

## Name
odh-ai-helpers:aipcc-fix-pr-commit

## Synopsis
```
/aipcc:fix-pr-commit           # Fix commits on current branch
/aipcc:fix-pr-commit AIPCC-123 # Fix commits with explicit JIRA ticket
```

## Description
Fixes non-compliant commits on a pull request branch by soft-resetting to the merge base, then creating a single compliant commit. This is useful when CI fails due to commit message format violations.

**Use cases:**
- Fix commits that failed JIRA ticket linter validation
- Squash multiple WIP commits into a single clean commit
- Rewrite commits missing required `Signed-off-by:` line

## Implementation

### Context Gathering
First, gather the current repository state:
- Run `git status` to see any uncommitted changes
- Run `git branch --show-current` to get current branch
- Run `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'` to get default branch
- Run `git log --oneline $(git merge-base HEAD origin/main)..HEAD` to see commits to fix

### Step 1: Stash Uncommitted Changes

If there are uncommitted changes:
```bash
git stash push -m "aipcc-fix-pr-commit: temporary stash"
```

### Step 2: Identify Base Branch

Determine the merge base (usually `main` or `master`):
```bash
git merge-base HEAD origin/main
```

### Step 3: Soft Reset

Reset to merge base while keeping all changes staged:
```bash
git reset --soft $(git merge-base HEAD origin/main)
```

### Step 4: Infer JIRA Ticket

Look for the JIRA ticket in (priority order):
1. Command argument (if provided)
2. Branch name (e.g., `AIPCC-1234-fix-something`)
3. Existing commit messages
4. PR/MR title or description

If unable to determine, ask the user before proceeding.

### Step 5: Create Compliant Commit

Create a single commit with all changes:

```bash
git commit --signoff -m "$(cat <<'EOF'
<JIRA-TICKET>: <Short description>

<Longer description summarizing all the changes>

Co-authored-by: <model>@<version> (claude code)
Signed-off-by: <Author Name> <email>
EOF
)"
```

**Commit Message Requirements:**
1. **Title line**: Must start with JIRA ticket ID matching: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX:`
2. **Body**: Must include at least one line of description after an empty line
3. **Co-authored-by**: When AI assisted, include `Co-authored-by: <model>@<version> (claude code)`
4. **Signed-off-by**: Must include a `Signed-off-by:` line

### Step 6: Validate Commit

Verify the commit message meets all requirements:
- [ ] Subject starts with valid JIRA prefix
- [ ] Blank line between subject and body
- [ ] Body contains at least one descriptive sentence
- [ ] `Signed-off-by:` line present

If validation fails, fix with `git commit --amend --signoff`

### Step 7: Force Push

Update the remote branch:
```bash
git push --force-with-lease origin <branch-name>
```

### Step 8: Restore Stashed Changes

If changes were stashed in Step 1:
```bash
git stash pop
```

## Examples

### Before (non-compliant commits)
```
abc1234 fix typo
def5678 add feature
ghi9012 WIP
jkl3456 more fixes
```

### After running command
```bash
/aipcc:fix-pr-commit AIPCC-1234
```

Results in single compliant commit:
```
AIPCC-1234: Add new validation feature

Implement input validation with typo fixes and additional features.
Includes all work from the original WIP commits.

Co-authored-by: claude-sonnet-4@20250514 (claude code)
Signed-off-by: Jane Developer <jane@redhat.com>
```

### Fix commits on existing PR
```bash
# On branch INFERENG-5678-my-feature with 3 non-compliant commits
/aipcc:fix-pr-commit
```

Infers `INFERENG-5678` from branch name and creates compliant commit.

## Arguments

- **[JIRA-TICKET]** (optional): JIRA ticket ID to use
  - If omitted: Inferred from branch name or existing commits
  - Format: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX`

## See Also
- **`/aipcc:commit`** – Create a new compliant commit
- **`/aipcc:commit-push-pr`** – Full workflow for new PRs
- **`/aipcc:commit-suggest`** – Generate commit message suggestions
- **`aipcc-commit-validator`** skill – Validate commits with the standalone script
