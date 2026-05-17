#!/bin/bash
# Push the sync branch and open a GitHub PR to the target repo.
#
# Usage:
#   bash open-pr.sh \
#     --repo /path/to/repo \
#     --branch sync/upstream-abc1234 \
#     --target-repo opendatahub-io/workload-variant-autoscaler \
#     --target-branch main \
#     --upstream-repo llm-d/llm-d-workload-variant-autoscaler \
#     --upstream-branch main \
#     --full-sha abc1234... \
#     --short-sha abc1234
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
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "${REPO}" || -z "${BRANCH}" || -z "${TARGET_REPO}" || -z "${UPSTREAM_REPO}" || -z "${FULL_SHA}" || -z "${SHORT_SHA}" ]]; then
  echo "Error: --repo, --branch, --target-repo, --upstream-repo, --full-sha, and --short-sha are required" >&2
  exit 1
fi

# Push to origin
git -C "${REPO}" push -u origin "${BRANCH}" 2>&1

# Verify push
if ! git -C "${REPO}" ls-remote --heads origin "${BRANCH}" | grep -q "${BRANCH}"; then
  echo "Error: push verification failed" >&2
  exit 1
fi
echo "Branch pushed to origin/${BRANCH}"

# Extract fork owner from origin URL (not gh repo view — resolves to parent on forks)
FORK_OWNER=$(git -C "${REPO}" remote get-url origin \
  | sed -E 's|.*[:/]([^/]+)/[^/]+(.git)?$|\1|')

if [[ -z "${FORK_OWNER}" ]]; then
  echo "Error: failed to extract fork owner from origin URL" >&2
  exit 1
fi

# Create PR
if PR_URL=$(gh pr create \
  --repo "${TARGET_REPO}" \
  --base "${TARGET_BRANCH}" \
  --head "${FORK_OWNER}:${BRANCH}" \
  --title "[sync] upstream ${UPSTREAM_REPO} ${SHORT_SHA} [$(date -u +%Y-%m-%d)]" \
  --body "$(cat <<EOF
Syncs ${UPSTREAM_REPO} ${UPSTREAM_BRANCH} into ${TARGET_REPO} ${TARGET_BRANCH}.

Upstream commit: https://github.com/${UPSTREAM_REPO}/commit/${FULL_SHA}
EOF
)" 2>&1); then
  printf 'PR_URL\t%s\n' "${PR_URL}"
else
  echo "PR creation failed. Create manually:" >&2
  echo "https://github.com/${TARGET_REPO}/compare/${TARGET_BRANCH}...${FORK_OWNER}:${BRANCH}" >&2
  exit 1
fi
