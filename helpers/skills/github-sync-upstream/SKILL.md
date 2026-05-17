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
  author: zdtsw
  version: "1.0"
  tags: github, sync, upstream, fork, merge, llm-d
---

# Sync Upstream

Merge upstream commits into a sync branch on the user's fork and open a
PR to the target repo. See `references/workflow.md` for exact script
invocations, exit-code handling, and the summary template.

**Commit SHA (optional):** `$ARGUMENTS`

## Step 1: Determine Working Context

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || REPO_ROOT=""
```

If `REPO_ROOT` is non-empty, run `detect-remotes.sh --repo "${REPO_ROOT}"`
and ask via `AskUserQuestion` whether this is the correct repo.
If yes → Step 2A. If no or not in a repo → Step 2B.

## Step 2A: In-Repo Setup

Pre-fill upstream/target from detect-remotes output. Ask via
`AskUserQuestion` to confirm: upstream repo, target repo, branches
(default `main`). Run `setup-remotes.sh`, parse `UPSTREAM_REMOTE` and
`TARGET_REMOTE`. Save `ORIGINAL_BRANCH` from current HEAD.

## Step 2B: Clone From Scratch

Ask for upstream repo, target repo, and branches. If the user has a
local clone, use its path and continue as Step 2A. If not, ask if they
have a GitHub fork — run `clone-fork.sh` then `setup-remotes.sh`. If
no fork exists, ask them to create one and re-run. **Stop.**

Save `ORIGINAL_BRANCH` from current HEAD.

## Step 3: Protected Files

Protected files keep the target version, discarding upstream changes.
If the repo name contains `llm-d`, auto-set
`OWNERS* .tekton/*.yaml Dockerfile*konflux` and confirm. Otherwise ask
for glob patterns (or none).

## Step 4: Pre-flight Check

Verify `origin` does not point to upstream or target. If it does, tell
the user to set origin to their personal fork and stop.

## Step 5: Merge

Run `sync-merge.sh`. Handle exit codes 0 (success), 1 (conflicts), and
3 (duplicate branch) as described in `references/workflow.md`.

## Step 6: Push and Open PR

Show PR summary and ask via `AskUserQuestion`: open a PR or just push?
If confirmed, run `open-pr.sh`.

## Step 7: Cleanup and Summary

Check out `ORIGINAL_BRANCH`. For Path B clones, inform the user of the
temp directory. Display the summary per `references/workflow.md`.
