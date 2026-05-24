#!/usr/bin/env bash
# Create a release branch on a GitHub repo via the GitHub API.
# Idempotent: if the branch already exists, reports "exists" and exits 0.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
create-release-branch.sh — create a release branch on a GitHub repo.

Required:
  --repo <owner/repo>     Target GitHub repo
  --branch <name>         Branch to create (e.g. release-v3.5-ea2)
  --base <ref>            Base ref: branch name (e.g. main) OR a 7–40 char
                          commit SHA. SHA is used verbatim; branch is
                          resolved to its current head SHA.

Optional:
  -h, --help              Show this help

Output (stdout, key=value lines): status, branch, sha, url.
Idempotent: status=exists when the branch is already present.
EOF
    exit 0
fi

REPO=""
BRANCH=""
BASE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)        REPO="$2";   shift 2 ;;
        --branch)      BRANCH="$2"; shift 2 ;;
        --base)        BASE="$2";   shift 2 ;;
        # Accepted for backward compatibility; treat as --base.
        --base-branch) BASE="$2";   shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [ -z "${REPO}" ] || [ -z "${BRANCH}" ] || [ -z "${BASE}" ]; then
    echo "missing required arg (need --repo, --branch, --base)" >&2
    exit 2
fi

if gh api "repos/${REPO}/branches/${BRANCH}" --jq '.name' >/dev/null 2>&1; then
    existing_sha=$(gh api "repos/${REPO}/branches/${BRANCH}" --jq '.commit.sha')
    printf 'status=exists\nbranch=%s\nsha=%s\nurl=https://github.com/%s/tree/%s\n' \
        "${BRANCH}" "${existing_sha:0:7}" "${REPO}" "${BRANCH}"
    exit 0
fi

# A 7–40 character hex string is treated as a commit SHA and used verbatim.
# Anything else is treated as a branch name and resolved via the refs API.
if [[ "${BASE}" =~ ^[0-9a-fA-F]{7,40}$ ]]; then
    # Verify the SHA exists in the repo (returns 404 if not).
    base_sha=$(gh api "repos/${REPO}/commits/${BASE}" --jq '.sha')
else
    base_sha=$(gh api "repos/${REPO}/git/ref/heads/${BASE}" --jq '.object.sha')
fi

gh api "repos/${REPO}/git/refs" \
    -f "ref=refs/heads/${BRANCH}" \
    -f "sha=${base_sha}" \
    >/dev/null

created_sha=$(gh api "repos/${REPO}/branches/${BRANCH}" --jq '.commit.sha')
printf 'status=created\nbranch=%s\nsha=%s\nurl=https://github.com/%s/tree/%s\n' \
    "${BRANCH}" "${created_sha:0:7}" "${REPO}" "${BRANCH}"
