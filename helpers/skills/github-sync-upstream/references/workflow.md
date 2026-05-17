# Workflow Details

## Script Invocations

### detect-remotes.sh

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/detect-remotes.sh" --repo "${REPO_ROOT}"
```

Output: tab-separated `name\towner/repo` per remote.

### setup-remotes.sh

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup-remotes.sh" \
  --repo "${REPO_ROOT}" \
  --upstream-repo "${UPSTREAM_REPO}" \
  --target-repo "${TARGET_REPO}" \
  --upstream-branch "${UPSTREAM_BRANCH}" \
  --target-branch "${TARGET_BRANCH}"
```

Output: `UPSTREAM_REMOTE\t<name>` and `TARGET_REMOTE\t<name>`.

### clone-fork.sh

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/clone-fork.sh" \
  --fork-repo "${FORK_REPO}" \
  --upstream-repo "${UPSTREAM_REPO}" \
  --target-repo "${TARGET_REPO}"
```

Output: `REPO_ROOT\t<path>`.

### sync-merge.sh

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/sync-merge.sh" \
  --repo "${REPO_ROOT}" \
  --upstream-remote "${UPSTREAM_REMOTE}" \
  --upstream-branch "${UPSTREAM_BRANCH}" \
  --target-remote "${TARGET_REMOTE}" \
  --target-branch "${TARGET_BRANCH}" \
  --upstream-repo "${UPSTREAM_REPO}" \
  --protected-patterns "${PROTECTED_PATTERNS}" \
  ${ARGUMENTS:+--commit "${ARGUMENTS}"}
```

Exit codes:

- **0**: clean merge. Output: `BRANCH`, `FULL_SHA`, `SHORT_SHA`,
  `COMMIT_COUNT` (tab-separated).
- **1**: unresolved conflicts. Prints `UNRESOLVED_CONFLICTS` or
  `CONFLICT_MARKERS_FOUND` with file details. Show to user, help
  resolve, re-stage and commit. If unresolvable:
  ```bash
  git -C "${REPO_ROOT}" merge --abort
  git -C "${REPO_ROOT}" checkout "${ORIGINAL_BRANCH}"
  git -C "${REPO_ROOT}" branch -D "${BRANCH}"
  ```
- **3**: duplicate branch exists. Prints `DUPLICATE_BRANCH` lines.
  Ask user whether to delete and re-run, or abort.

### open-pr.sh

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/open-pr.sh" \
  --repo "${REPO_ROOT}" \
  --branch "${BRANCH}" \
  --target-repo "${TARGET_REPO}" \
  --target-branch "${TARGET_BRANCH}" \
  --upstream-repo "${UPSTREAM_REPO}" \
  --upstream-branch "${UPSTREAM_BRANCH}" \
  --full-sha "${FULL_SHA}" \
  --short-sha "${SHORT_SHA}"
```

Output: `PR_URL\t<url>`.

## Summary Template

```text
Sync completed successfully

- Branch: sync/upstream-<short_sha> pushed to origin
- PR: <target_repo>#<pr_number>           (omit if skipped)
- URL: <pr_url>                           (omit if skipped)
- Syncs: <N> commits from <upstream_repo> <upstream_branch> (<short_sha>)
         into <target_repo> <target_branch>
- Protected files restored: <patterns>    (omit if none)
- Conflicts resolved: <file> (<details>)  (omit if none)
- Returned to: <original_branch> branch
```

## Gotchas

- **Fork owner detection**: Always extract from `origin` remote URL, not
  `gh repo view --json owner` (resolves to parent on forks).
- **SSH vs HTTPS URLs**: The sed pattern in scripts handles both formats.
- **Protected file globs**: Matched against the basename, so
  `Dockerfile*konflux` matches `services/foo/Dockerfile.konflux`.
- **Conflict markers after clean merge**: `sync-merge.sh` always scans.
