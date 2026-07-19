#!/bin/bash
# Push the sync branch and open a GitHub PR to the target repo.
#
# Usage:
#   bash open-pr.sh \
#     --repo /path/to/repo \
#     --branch sync/upstream-abc1234 \
#     --target-repo target-org/my-project \
#     --target-branch main \
#     --upstream-repo upstream-org/my-project \
#     --upstream-branch main \
#     --full-sha abc1234... \
#     --short-sha abc1234 \
#     [--conflicts "$(printf '| `OWNERS` | kept ours | ODH-owned |\n')"] \
#     [--assignee <github-handle>]
#
# --conflicts is optional: markdown table rows (no header) describing how
# conflicts were resolved. When supplied, a "## Conflict Resolution" section
# is appended. Commit count and diffstat are derived automatically from the
# sync merge commit's two parents.
#
# --assignee is optional: after the PR is created it is assigned (best-effort;
# a failed assignment does not fail the script). Assigning the PR author is
# allowed — unlike requesting review from the author.
#
# Idempotent: if an open PR already exists for the head branch, its PR_URL is
# printed and the script exits 0 WITHOUT pushing or creating a duplicate.
#
# Output on success:
#   PR_URL	https://github.com/...

set -euo pipefail

REPO=""
BRANCH=""
TARGET_REPO=""
TARGET_BRANCH="main"
UPSTREAM_REPO=""
UPSTREAM_BRANCH="main"
FULL_SHA=""
SHORT_SHA=""
CONFLICTS=""
ASSIGNEE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)             REPO="$2"; shift 2;;
    --branch)           BRANCH="$2"; shift 2;;
    --target-repo)      TARGET_REPO="$2"; shift 2;;
    --target-branch)    TARGET_BRANCH="$2"; shift 2;;
    --upstream-repo)    UPSTREAM_REPO="$2"; shift 2;;
    --upstream-branch)  UPSTREAM_BRANCH="$2"; shift 2;;
    --full-sha)         FULL_SHA="$2"; shift 2;;
    --short-sha)        SHORT_SHA="$2"; shift 2;;
    --conflicts)        CONFLICTS="$2"; shift 2;;
    --assignee)         ASSIGNEE="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "${REPO}" || -z "${BRANCH}" || -z "${TARGET_REPO}" || -z "${UPSTREAM_REPO}" || -z "${FULL_SHA}" || -z "${SHORT_SHA}" ]]; then
  echo "Error: --repo, --branch, --target-repo, --upstream-repo, --full-sha, and --short-sha are required" >&2
  exit 1
fi

# Extract fork owner from origin URL (not gh repo view — resolves to parent on forks)
FORK_OWNER=$(git -C "${REPO}" remote get-url origin \
  | sed -E 's|.*[:/]([^/]+)/[^/]+(.git)?$|\1|')

if [[ -z "${FORK_OWNER}" ]]; then
  echo "Error: failed to extract fork owner from origin URL" >&2
  exit 1
fi

# Fast-exit idempotency: if an open PR for this exact head branch already
# exists, don't push or recreate — just return its URL. Under sha-named sync
# branches, an existing PR means the same upstream tip is already in flight,
# so there is nothing new to push. A gh failure here degrades safely to the
# normal push/create path below.
EXISTING_PR=$(gh pr list --repo "${TARGET_REPO}" --state open \
  --head "${BRANCH}" \
  --json url,headRefName,headRepositoryOwner \
  --jq "[.[] | select(.headRefName==\"${BRANCH}\" and .headRepositoryOwner.login==\"${FORK_OWNER}\")][0].url // empty" \
  2>/dev/null || true)
if [[ -n "${EXISTING_PR}" ]]; then
  echo "PR already open for ${FORK_OWNER}:${BRANCH} — skipping push and creation." >&2
  printf 'PR_URL\t%s\n' "${EXISTING_PR}"
  exit 0
fi

# Push to origin
git -C "${REPO}" push -u origin "${BRANCH}" 2>&1

# Verify push
if ! git -C "${REPO}" ls-remote --heads origin "${BRANCH}" | grep -q "${BRANCH}"; then
  echo "Error: push verification failed" >&2
  exit 1
fi
echo "Branch pushed to origin/${BRANCH}"

# Derive sync stats from the merge commit. sync-merge.sh uses --no-ff, so the
# branch tip is a merge commit whose first parent is the target tip and whose
# second parent is the synced upstream commit.
MERGE_SHA=$(git -C "${REPO}" rev-parse "${BRANCH}")
NUM_PARENTS=$(( $(git -C "${REPO}" rev-list --parents -n1 "${MERGE_SHA}" | wc -w) - 1 ))

SUMMARY=""
if [[ "${NUM_PARENTS}" -ge 2 ]]; then
  COMMIT_COUNT=$(git -C "${REPO}" rev-list --count "${MERGE_SHA}^1..${MERGE_SHA}^2")
  DIFFSTAT=$(git -C "${REPO}" diff --shortstat "${MERGE_SHA}^1" "${MERGE_SHA}")
  FILES=$(grep -oE '[0-9]+ files? changed' <<<"${DIFFSTAT}" | grep -oE '[0-9]+' || echo 0)
  INS=$(grep -oE '[0-9]+ insertion' <<<"${DIFFSTAT}" | grep -oE '[0-9]+' || echo 0)
  DEL=$(grep -oE '[0-9]+ deletion' <<<"${DIFFSTAT}" | grep -oE '[0-9]+' || echo 0)
  SUMMARY=$(cat <<EOF

## Summary

- **${COMMIT_COUNT} commits** synced from ${UPSTREAM_BRANCH}
- **${FILES:-0} files changed**, +${INS:-0} / -${DEL:-0} lines
EOF
)
fi

CONFLICT_SECTION=""
if [[ -n "${CONFLICTS}" ]]; then
  CONFLICT_SECTION=$(cat <<EOF


## Conflict Resolution

| File | Resolution | Rationale |
|------|-----------|-----------|
${CONFLICTS}
EOF
)
fi

PR_BODY=$(cat <<EOF
Syncs ${UPSTREAM_REPO} ${UPSTREAM_BRANCH} into ${TARGET_REPO} ${TARGET_BRANCH}.

Upstream commit: https://github.com/${UPSTREAM_REPO}/commit/${FULL_SHA}
${SUMMARY}${CONFLICT_SECTION}
EOF
)

# Create PR
if PR_URL=$(gh pr create \
  --repo "${TARGET_REPO}" \
  --base "${TARGET_BRANCH}" \
  --head "${FORK_OWNER}:${BRANCH}" \
  --title "[sync] upstream ${UPSTREAM_REPO} ${SHORT_SHA} [$(date -u +%Y-%m-%d)]" \
  --body "${PR_BODY}" 2>&1); then
  printf 'PR_URL\t%s\n' "${PR_URL}"
  # Best-effort assignee: never fail an already-opened PR on an assign error.
  # (Assigning the PR author to their own PR IS allowed, unlike requesting
  # review from the author.)
  if [[ -n "${ASSIGNEE}" ]]; then
    if gh pr edit "${PR_URL}" --add-assignee "${ASSIGNEE}" >/dev/null 2>&1; then
      echo "Assigned ${ASSIGNEE}" >&2
    else
      echo "warn: could not assign ${ASSIGNEE} to ${PR_URL}" >&2
    fi
  fi
else
  echo "PR creation failed. Create manually:" >&2
  echo "https://github.com/${TARGET_REPO}/compare/${TARGET_BRANCH}...${FORK_OWNER}:${BRANCH}" >&2
  exit 1
fi
