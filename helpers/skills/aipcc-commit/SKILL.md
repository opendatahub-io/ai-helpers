---
name: aipcc-commit
description: Create, push, fix, or suggest git commits following AIPCC (AI Platform Core Components) conventions. Supports commit, push+PR, fix/squash, suggestion, and validation modes.
allowed-tools: Bash Read
user-invocable: true
---

# AIPCC Commit

Create git commits following the AIPCC (AI Platform Core Components) commit message format required by Red Hat AI projects using GitLab's JIRA ticket linter.

## Modes

This skill operates in four modes based on arguments:

| Invocation | Mode | Description |
|------------|------|-------------|
| `/aipcc:commit [TICKET]` | Commit | Stage + commit with AIPCC format |
| `/aipcc:commit --push [TICKET]` | Push + PR | Commit + push + create PR/MR |
| `/aipcc:commit --fix [TICKET]` | Fix | Squash and rewrite non-compliant PR commits |
| `/aipcc:commit --suggest [N]` | Suggest | Generate message suggestions without committing |
| `/aipcc:commit --validate [REF]` | Validate | Validate commit messages against AIPCC linter rules |

## Commit Message Format

All commits MUST follow this exact format:

```
<JIRA-TICKET>: <Short description>

<Longer description explaining what changed and why>

Co-authored-by: <model>@<version> (claude code)
Signed-off-by: <Author Name> <email>
```

### Validation Rules

1. **Title line**: Must start with a JIRA ticket ID matching: `(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-\d+:`
2. **Body**: Must include at least one non-trailer line of description after a blank line (lines containing only `Signed-off-by:`, `Co-authored-by:`, or `Co-Authored-By:` do not count as body content)
3. **Co-authored-by**: When AI assisted, include `Co-authored-by: <model>@<version> (claude code)`
4. **Signed-off-by**: Must include a `Signed-off-by:` line (use `--signoff` flag)

## Instructions

### Context Gathering (All Modes)

First, gather the current repository state:
- Run `git status` to see staged/unstaged changes
- Run `git diff HEAD` to see all changes
- Run `git branch --show-current` to get current branch
- Run `git log --oneline -5` to see recent commit style
- Run `git remote -v` to detect GitHub vs GitLab

### JIRA Ticket Inference

Look for the JIRA ticket in priority order:
1. Command argument (if provided)
2. Branch name (e.g., `AIPCC-1234-fix-something`)
3. Existing commit messages
4. PR/MR title or description

If unable to determine, ask the user before proceeding.

---

### Mode: Commit (default)

**Triggered by:** `/aipcc:commit [TICKET]`

1. Stage files with `git add`
2. Create the commit using:
   ```bash
   git commit --signoff -m "$(cat <<'EOF'
   <commit message here>
   EOF
   )"
   ```
3. Validate the commit message meets all requirements
4. If validation fails, fix with `git commit --amend --signoff` and re-validate

---

### Mode: Push + PR (`--push`)

**Triggered by:** `/aipcc:commit --push [TICKET]`

Complete workflow: commit, push, and open a pull/merge request.

1. **Create feature branch** if on `main`/`master`:
   ```bash
   git checkout -b <JIRA-TICKET>-short-description
   ```

2. **Stage and commit** with AIPCC format (same as Commit mode)

3. **Validate** the commit message

4. **Push** to remote:
   ```bash
   git push -u origin <branch-name>
   ```

5. **Create PR/MR** based on remote type:

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

---

### Mode: Fix (`--fix`)

**Triggered by:** `/aipcc:commit --fix [TICKET]`

Fix non-compliant commits on a PR branch by soft-resetting to the merge base, then creating a single compliant commit.

1. **Stash uncommitted changes** if any:
   ```bash
   git stash push -m "aipcc-commit-fix: temporary stash"
   ```

2. **Identify base branch** and merge base:
   ```bash
   git merge-base HEAD origin/main
   ```

3. **Log commits to fix:**
   ```bash
   git log --oneline $(git merge-base HEAD origin/main)..HEAD
   ```

4. **Soft reset** to merge base:
   ```bash
   git reset --soft $(git merge-base HEAD origin/main)
   ```

5. **Create a single compliant commit** with all changes (same format as Commit mode)

6. **Validate** the commit message

7. **Force push** to update the remote branch:
   ```bash
   git push --force-with-lease origin <branch-name>
   ```

8. **Restore stashed changes** if any:
   ```bash
   git stash pop
   ```

---

### Mode: Suggest (`--suggest`)

**Triggered by:** `/aipcc:commit --suggest [N]`

Generate commit message suggestions without committing.

**Mode 1 (no N):** Analyze staged changes
1. Collect staged changes via `git diff --cached`
2. Analyze file paths and code to determine appropriate JIRA ticket
3. Generate 3 suggestions (Recommended, Standard, Minimal)
4. Ask user: "Which suggestion would you like to use? (1/2/3 or skip)"
5. If user selects one, execute `git commit -s` with that message

**Mode 2 (with N):** Analyze last N commits
1. Retrieve last N commits using `git log`
2. For **N=1**: Suggest improved rewrite following AIPCC format
3. For **N>=2**: Generate unified squash message with footer: `Squashed from N commits:` + original commit list
4. Generate 3 suggestions and prompt for selection
5. Execute `git commit --amend -s` (N=1) or squash operation (N>=2) if requested

**Suggestion format:**
```
Suggestion #1 (Recommended)
AIPCC-123: Add JWT authentication middleware

Implement token-based authentication for API endpoints to enhance
security. The middleware verifies JWT tokens and extracts user
information for authorization decisions.

Co-authored-by: <model>@<version> (claude code)
Signed-off-by: Your Name <your.email@example.com>
```

---

### Mode: Validate (`--validate`)

**Triggered by:** `/aipcc:commit --validate [REF]`

Validate commit messages against AIPCC linter rules. Mimics the JIRA ticket linter used in GitLab CI.

**IMPORTANT**: Run the script from the user's git repository directory, not from the skill directory. Use the base directory (`<base_path>`) for this skill to execute the script with an absolute path.

**Validate last commit:**
```bash
uv run <base_path>/scripts/validate_commit.py
```

**Validate a specific commit:**
```bash
uv run <base_path>/scripts/validate_commit.py <commit-sha>
```

**Validate a range of commits:**
```bash
uv run <base_path>/scripts/validate_commit.py origin/main..HEAD
```

**Validate multiple specific commits:**
```bash
uv run <base_path>/scripts/validate_commit.py abc1234 def5678
```

**Example output (success):**
```
✓ All 3 commit(s) pass AIPCC linter validation
```

**Example output (failure):**
```
✗ Commit validation failed:

  [abc1234] Subject must start with JIRA ticket (RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX:
    Got: fix typo in readme...

  [abc1234] Commit must have a body (description after blank line)

  [abc1234] Commit must include 'Signed-off-by: Name <email@domain>'
    Use: git commit --signoff
```

**Prerequisites:** Git repository, Python 3.10+ with `uv` installed (script is self-contained).
