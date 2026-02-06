---
description: Commit, push, and open a PR/MR following AIPCC conventions
argument-hint: [JIRA-TICKET]
---

## Name
odh-ai-helpers:aipcc-commit-push-pr

## Synopsis
```
/aipcc:commit-push-pr           # Full workflow with inferred JIRA ticket
/aipcc:commit-push-pr AIPCC-123 # Full workflow with explicit JIRA ticket
```

## Description
Complete workflow command that creates a commit, pushes to remote, and opens a pull/merge request in one operation. Handles both GitHub (using `gh`) and GitLab (using `glab`) repositories.

**Workflow:**
1. Create feature branch if on main
2. Stage and commit changes with AIPCC format
3. Validate commit message
4. Push branch to origin
5. Create PR/MR with proper description

## Implementation

### Context Gathering
First, gather the current repository state:
- Run `git status` to see staged/unstaged changes
- Run `git diff HEAD` to see all changes
- Run `git branch --show-current` to get current branch
- Run `git remote -v` to detect GitHub vs GitLab

### Step 1: Create Branch If Needed

If on `main` or `master`, create a feature branch:
```bash
git checkout -b <JIRA-TICKET>-short-description
```

Branch naming convention: `AIPCC-1234-short-description`

### Step 2: Commit Message Format

The commit message MUST follow this exact format:

```
<JIRA-TICKET>: <Short description>

<Longer description explaining what changed and why>

Co-authored-by: <model>@<version> (claude code)
Signed-off-by: <Author Name> <email>
```

**Requirements:**
1. **Title line**: Must start with JIRA ticket ID matching: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX:`
2. **Body**: Must include at least one line of description after an empty line
3. **Co-authored-by**: When AI assisted, include `Co-authored-by: <model>@<version> (claude code)`
4. **Signed-off-by**: Must include a `Signed-off-by:` line (use `--signoff` flag)

### Step 3: Create Commit

```bash
git add <files>
git commit --signoff -m "$(cat <<'EOF'
<JIRA-TICKET>: <Short description>

<Longer description>

Co-authored-by: <model>@<version> (claude code)
Signed-off-by: <Author Name> <email>
EOF
)"
```

### Step 4: Validate Commit

Verify the commit message meets all requirements:
- [ ] Subject starts with valid JIRA prefix
- [ ] Blank line between subject and body
- [ ] Body contains at least one descriptive sentence
- [ ] `Signed-off-by:` line present

If validation fails, fix with `git commit --amend --signoff`

### Step 5: Push to Remote

```bash
git push -u origin <branch-name>
```

### Step 6: Create PR/MR

**For GitHub:**
```bash
gh pr create --title "<JIRA-TICKET>: <description>" --body "$(cat <<'EOF'
## Summary

<Description of changes>

## Test Plan

- [ ] Tests pass locally
- [ ] Manual testing completed

Signed-off-by: <Author Name> <email>
EOF
)"
```

**For GitLab:**
```bash
glab mr create --title "<JIRA-TICKET>: <description>" --description "$(cat <<'EOF'
## Summary

<Description of changes>

## Test Plan

- [ ] Tests pass locally
- [ ] Manual testing completed

Signed-off-by: <Author Name> <email>
EOF
)"
```

### MR/PR Description Format

The MR/PR description MUST include a `Signed-off-by:` line at the end:

```
<Description of the changes>

Signed-off-by: <Author Name> <email>
```

## Examples

### Complete workflow
```bash
# Make changes to files
/aipcc:commit-push-pr AIPCC-1234
```

This will:
1. Create branch `AIPCC-1234-feature-description` (if needed)
2. Stage and commit with proper message
3. Push to origin
4. Create PR/MR

### GitLab project
```bash
/aipcc:commit-push-pr INFERENG-5678
```
Uses `glab mr create` for GitLab repos.

## Arguments

- **[JIRA-TICKET]** (optional): JIRA ticket ID to use
  - If omitted: Inferred from branch name
  - Format: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX`

## See Also
- **`/aipcc:commit`** – Create just the commit without push/PR
- **`/aipcc:fix-pr-commit`** – Fix commits on existing PRs
- **`/aipcc:commit-suggest`** – Generate commit message suggestions
- **`aipcc-commit-validator`** skill – Validate commits with the standalone script
