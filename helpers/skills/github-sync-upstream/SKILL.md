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
  tags: github, sync, upstream, fork, merge
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

If `REPO_ROOT` is non-empty, run `scripts/detect-remotes.sh --repo "${REPO_ROOT}"`
and ask via `AskUserQuestion` whether this is the correct repo.
If yes → Step 2A. If no or not in a repo → Step 2B.

## Step 2A: In-Repo Setup

Pre-fill upstream/target from detect-remotes output. Ask via
`AskUserQuestion` to confirm: upstream repo, target repo, branches
(default `main`). Run `scripts/setup-remotes.sh`, parse `UPSTREAM_REMOTE` and
`TARGET_REMOTE`. Save `ORIGINAL_BRANCH` from current HEAD.

## Step 2B: Clone From Scratch

Ask for upstream repo, target repo, and branches. If the user has a
local clone, use its path and continue as Step 2A. If not, ask if they
have a GitHub fork — run `scripts/clone-fork.sh` then `scripts/setup-remotes.sh`. If
no fork exists, ask them to create one and re-run. **Stop.**

Save `ORIGINAL_BRANCH` from current HEAD.

## Step 3: Protected Files

Protected files keep the target version, discarding upstream changes.
Ask via `AskUserQuestion` for glob patterns to protect (or none).
Suggest common examples: `/OWNERS`, `/OWNERS_ALIASES`, `.tekton/*.yaml`,
`Dockerfile*konflux`.

Anchor ownership patterns to the repo root with a leading `/`. A bare
`OWNERS*` matches by basename and so also deletes nested OWNERS files that
upstream owns (e.g. `pkg/.../OWNERS`), which is rarely intended — only the
root `OWNERS` / `OWNERS_ALIASES` are usually target-specific.

## Step 4: Pre-flight Check

Verify `origin` does not point to upstream or target. If it does, tell
the user to set origin to their personal fork and stop.

## Step 5: Merge

Run `scripts/sync-merge.sh`. Handle exit codes 0 (success), 1 (conflicts),
3 (duplicate branch — a sync PR for this tip already exists), and 4 (nothing
to sync — target already up to date; report and stop, no PR) as described in
`references/workflow.md`.

When an agent is driving this skill, pass `--co-author "Claude
<noreply@anthropic.com>"` so the merge commit credits the agent alongside the
human author.

## Step 6: Push and Open PR

Show PR summary and ask via `AskUserQuestion`: open a PR or just push?
If confirmed, run `scripts/open-pr.sh`. The PR body's commit count and
diffstat are derived automatically from the merge commit. If any conflicts
were resolved in Step 5, pass them via `--conflicts` (markdown table rows,
no header) so a "## Conflict Resolution" section is appended.

To put a human on the PR, pass `--assignee <handle>` (assignee, **not**
reviewer — GitHub forbids requesting review from the PR author, so a
`--reviewer` equal to the author is silently dropped). `open-pr.sh` is
idempotent: if an open PR for the branch already exists it returns that URL
without creating a duplicate.

## Step 7: Cleanup and Summary

Check out `ORIGINAL_BRANCH`. Then, **if the sync branch was successfully
pushed in Step 6**, delete the now-redundant *local* sync branch
(`git branch -D <sync-branch>`): the PR tracks the branch pushed to the fork
(`origin`), so the local copy is no longer needed. Never delete the *remote*
branch — the open PR depends on it. If the push failed (no PR was opened),
**keep** the local branch so the work can be retried.

For Path B (clone-from-scratch) the entire temp clone is discarded, so there
is no local branch to clean up — just inform the user of the temp directory.

Display the summary per `references/workflow.md`.
