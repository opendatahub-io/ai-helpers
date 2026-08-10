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
  ${CO_AUTHOR:+--co-author "${CO_AUTHOR}"} \
  ${ARGUMENTS:+--commit "${ARGUMENTS}"}
```

`--co-author` is optional; pass it (e.g. `Claude <noreply@anthropic.com>`) to
credit the agent driving the sync as a `Co-authored-by:` trailer on the merge
commit, alongside the human author.

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
- **3**: duplicate branch exists. Prints `DUPLICATE_BRANCH` lines. Means a
  sync branch for this exact upstream tip already exists (e.g. a prior sync
  PR is still open). Ask the user whether to delete and re-run, or abort.
- **4**: nothing to sync — the target already contains the upstream tip
  (e.g. the previous sync PR was merged, or the fork is already current).
  Prints `NOTHING_TO_SYNC` plus `FULL_SHA`/`SHORT_SHA`/`COMMIT_COUNT 0`. No
  branch is created. Report "already up to date" and stop; do not open a PR.

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
  --short-sha "${SHORT_SHA}" \
  ${CONFLICTS:+--conflicts "${CONFLICTS}"} \
  ${ASSIGNEE:+--assignee "${ASSIGNEE}"}
```

Output: `PR_URL\t<url>`. `--assignee` is optional (best-effort; assigning the
PR author is allowed). If an open PR for the head branch already exists,
open-pr.sh prints that PR's URL and exits 0 without pushing or duplicating.

The PR body includes a `## Summary` section with commit count and diffstat,
derived automatically from the sync merge commit's two parents (parent 1 =
target tip, parent 2 = synced upstream commit). `--conflicts` is optional:
pass markdown table rows (no header), one per resolved conflict, e.g.
`` | `OWNERS` | kept ours | ODH-owned file | ``. When supplied, a
`## Conflict Resolution` section is appended.

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
- **Protected file globs**: A bare pattern matches the basename anywhere, so
  `Dockerfile*konflux` matches `services/foo/Dockerfile.konflux`. A pattern
  with `/` matches the relative path, so `.tekton/*.yaml` matches
  `.tekton/pipeline.yaml`. A leading `/` anchors to the repo root, so
  `/OWNERS` matches only the top-level `OWNERS` — not nested `pkg/.../OWNERS`
  files that upstream owns. Prefer `/OWNERS /OWNERS_ALIASES` over `OWNERS*`.
- **Conflict markers after clean merge**: `sync-merge.sh` always scans.
