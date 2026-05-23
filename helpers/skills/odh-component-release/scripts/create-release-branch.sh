#!/usr/bin/env bash
# Create a release branch on a GitHub repo via the GitHub API.
# Idempotent: if the branch already exists, reports "exists" and exits 0.
#
# Usage:
#   create-release-branch.sh --repo <owner/repo> --branch <branch> \
#                            --base-branch <base> [--dry-run]
#
# Output (stdout, one key=value per line):
#   status=created|exists|would-create
#   branch=<branch>
#   sha=<short-sha>
#   url=<browser-url>

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
create-release-branch.sh — create a release branch on a GitHub repo.

Required:
  --repo <owner/repo>     Target GitHub repo
  --branch <name>         Branch to create (e.g. release-v0.5.0)
  --base-branch <name>    Branch to fork from (e.g. main)

Optional:
  --dry-run               Report what would happen; do not create
  -h, --help              Show this help

Output (stdout, key=value lines): status, branch, sha, url.
Idempotent: status=exists when the branch is already present.
EOF
    exit 0
fi

REPO=""
BRANCH=""
BASE_BRANCH=""
DRY_RUN="false"

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)        REPO="$2";        shift 2 ;;
        --branch)      BRANCH="$2";      shift 2 ;;
        --base-branch) BASE_BRANCH="$2"; shift 2 ;;
        --dry-run)     DRY_RUN="true";   shift ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [ -z "${REPO}" ] || [ -z "${BRANCH}" ] || [ -z "${BASE_BRANCH}" ]; then
    echo "missing required arg (need --repo, --branch, --base-branch)" >&2
    exit 2
fi

if gh api "repos/${REPO}/branches/${BRANCH}" --jq '.name' >/dev/null 2>&1; then
    existing_sha=$(gh api "repos/${REPO}/branches/${BRANCH}" --jq '.commit.sha')
    printf 'status=exists\nbranch=%s\nsha=%s\nurl=https://github.com/%s/tree/%s\n' \
        "${BRANCH}" "${existing_sha:0:7}" "${REPO}" "${BRANCH}"
    exit 0
fi

base_sha=$(gh api "repos/${REPO}/git/ref/heads/${BASE_BRANCH}" --jq '.object.sha')

if [ "${DRY_RUN}" = "true" ]; then
    printf 'status=would-create\nbranch=%s\nsha=%s\nurl=https://github.com/%s/tree/%s\n' \
        "${BRANCH}" "${base_sha:0:7}" "${REPO}" "${BRANCH}"
    exit 0
fi

gh api "repos/${REPO}/git/refs" \
    -f "ref=refs/heads/${BRANCH}" \
    -f "sha=${base_sha}" \
    >/dev/null

# Confirm visible via the branches endpoint.
created_sha=$(gh api "repos/${REPO}/branches/${BRANCH}" --jq '.commit.sha')
printf 'status=created\nbranch=%s\nsha=%s\nurl=https://github.com/%s/tree/%s\n' \
    "${BRANCH}" "${created_sha:0:7}" "${REPO}" "${BRANCH}"
