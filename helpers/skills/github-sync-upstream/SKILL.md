---
name: github-sync-upstream
description: >-
  Sync code from an upstream GitHub repository into a target fork
  (e.g., opendatahub-io midstream). Detects remotes from the current repo,
  or clones fresh if run from outside. Fetches upstream, merges into a sync
  branch, restores protected files, resolves conflicts, and opens a PR to
  the target GitHub repo. Use when asked to sync upstream, merge upstream
  changes, or bring a GitHub fork up to date with its upstream source.
allowed-tools: Bash Read AskUserQuestion
user-invocable: true
argument-hint: "[commit-sha]"
compatibility: Requires git. gh CLI (authenticated) needed only for PR creation.
metadata:
  author: Wen Zhou
  version: "1.0"
  tags: github, sync, upstream, fork, merge, llm-d
---

# Sync Upstream

Sync code from an upstream GitHub repository into a target fork
(e.g., opendatahub-io midstream). Merges upstream commits into a new
branch on the user's fork and opens a PR to the target GitHub
organization repo.

**Commit SHA (optional):** `$ARGUMENTS`

## Step 1: Determine Working Context

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || REPO_ROOT=""
```

If `REPO_ROOT` is non-empty, run the detect-remotes script:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/detect-remotes.sh" --repo "${REPO_ROOT}"
```

Show the output and ask via `AskUserQuestion`: "Is this repo
(`<origin owner/repo>`) where you want to open a PR with the synced
upstream code?"

- **Yes** → Path A (Step 2A)
- **No** → Path B (Step 2B)

If `REPO_ROOT` is empty → Path B (Step 2B).

## Step 2A: In-Repo Setup

The user is inside their fork. Using the detect-remotes output, identify
candidates for upstream and target repos.

Ask via `AskUserQuestion` to confirm or collect:

1. **Upstream repo** (`owner/repo`) — pre-fill if detected
2. **Target repo** (`owner/repo`) — pre-fill if detected
3. **Upstream branch** — default `main`
4. **Target branch** — default `main`

Run the setup-remotes script:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup-remotes.sh" \
  --repo "${REPO_ROOT}" \
  --upstream-repo "${UPSTREAM_REPO}" \
  --target-repo "${TARGET_REPO}" \
  --upstream-branch "${UPSTREAM_BRANCH}" \
  --target-branch "${TARGET_BRANCH}"
```

Parse `UPSTREAM_REMOTE` and `TARGET_REMOTE` from the output. Save
`ORIGINAL_BRANCH=$(git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD)`.

Continue to **Step 3**.

## Step 2B: Clone From Scratch

Ask via `AskUserQuestion` for:

1. **Upstream repo** (`owner/repo`)
2. **Target repo** (`owner/repo`)
3. **Upstream branch** — default `main`
4. **Target branch** — default `main`

Then ask: **Do you already have a local clone of your fork?**

- **Yes** → ask for the path, set `REPO_ROOT`, continue as Step 2A.
- **No** → ask: **Do you have a fork of `<TARGET_REPO>` on GitHub?**
  - **Yes** → ask for the fork (`owner/repo`), then clone it:
    ```bash
    bash "${CLAUDE_SKILL_DIR}/scripts/clone-fork.sh" \
      --fork-repo "${FORK_REPO}" \
      --upstream-repo "${UPSTREAM_REPO}" \
      --target-repo "${TARGET_REPO}"
    ```
    Parse `REPO_ROOT` from the output. Then run setup-remotes (Step 2A).
  - **No** → inform the user they need a fork of `<TARGET_REPO>` to
    push the sync branch. Ask them to create one (e.g., via the GitHub
    UI or any method they prefer) and re-run the skill. **Stop here.**

Set `ORIGINAL_BRANCH="${TARGET_BRANCH}"`. Continue to **Step 3**.

## Step 3: Determine Protected Files

If the repo name (from `UPSTREAM_REPO` or `TARGET_REPO`) contains
`llm-d`, auto-set and inform the user:

```bash
PROTECTED_PATTERNS="OWNERS* .tekton/*.yaml Dockerfile*konflux"
```

Ask via `AskUserQuestion`: "These files will be kept as they are in the
target repo (upstream changes will be discarded for them). Do you want
to change this list, or accept it as-is?"

Otherwise, ask via `AskUserQuestion`: "Are there files that should keep
the target version and ignore upstream changes? Provide space-separated
glob patterns, or leave empty for none. Example: `OWNERS* .tekton/*.yaml`"

## Step 4: Pre-flight Check

```bash
ORIGIN_URL=$(git -C "${REPO_ROOT}" remote get-url origin)
```

Verify `origin` does not point to upstream or target. If it does, tell
the user to set origin to their personal fork and stop.

## Step 5: Merge

Run the sync-merge script:

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

**If exit code 0**: parse `BRANCH`, `FULL_SHA`, `SHORT_SHA`,
`COMMIT_COUNT` from output. Continue to Step 6.

**If exit code 1 (conflicts)**: the script prints `UNRESOLVED_CONFLICTS`
or `CONFLICT_MARKERS_FOUND` with file details. Show these to the user,
help resolve them manually, then re-stage and commit. If unresolvable:

```bash
git -C "${REPO_ROOT}" merge --abort
git -C "${REPO_ROOT}" checkout "${ORIGINAL_BRANCH}"
git -C "${REPO_ROOT}" branch -D "${BRANCH}"
```

**If exit code 3 (duplicate branch)**: the script prints `DUPLICATE_BRANCH`
lines and exits without creating a branch. Ask the user whether to delete
the existing branch and re-run, or abort.

## Step 6: Push and Open PR

Show the PR summary (commits, files changed) and ask via
`AskUserQuestion`: open a PR or stop with the branch pushed?

If confirmed, run:

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

## Step 7: Cleanup and Summary

```bash
git -C "${REPO_ROOT}" checkout "${ORIGINAL_BRANCH}"
```

For Path B clones, inform the user of the temp directory location.

Display:

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
