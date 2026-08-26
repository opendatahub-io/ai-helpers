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

require_value() {
    if [ "$#" -lt 2 ] || [[ "$2" == --* ]]; then
        echo "missing value for $1" >&2
        exit 2
    fi
}

REPO=""
BRANCH=""
BASE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)        require_value "$@"; REPO="$2";   shift 2 ;;
        --branch)      require_value "$@"; BRANCH="$2"; shift 2 ;;
        --base)        require_value "$@"; BASE="$2";   shift 2 ;;
        # Accepted for backward compatibility; treat as --base.
        --base-branch) require_value "$@"; BASE="$2";   shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [ -z "${REPO}" ] || [ -z "${BRANCH}" ] || [ -z "${BASE}" ]; then
    echo "missing required arg (need --repo, --branch, --base)" >&2
    exit 2
fi

report_exists() {
    local sha
    sha=$(gh api "repos/${REPO}/branches/${BRANCH}" --jq '.commit.sha')
    printf 'status=exists\nbranch=%s\nsha=%s\nurl=https://github.com/%s/tree/%s\n' \
        "${BRANCH}" "${sha:0:7}" "${REPO}" "${BRANCH}"
}

if gh api "repos/${REPO}/branches/${BRANCH}" --jq '.name' >/dev/null 2>&1; then
    report_exists
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

# TOCTOU-safe create: if create fails because the ref already exists (a
# concurrent run beat us to it), report status=exists rather than failing.
create_err=""
if ! create_err=$(gh api "repos/${REPO}/git/refs" \
        -f "ref=refs/heads/${BRANCH}" \
        -f "sha=${base_sha}" 2>&1); then
    if gh api "repos/${REPO}/branches/${BRANCH}" --jq '.name' >/dev/null 2>&1; then
        report_exists
        exit 0
    fi
    echo "status=failed" >&2
    echo "error=${create_err}" >&2
    exit 1
fi

created_sha=$(gh api "repos/${REPO}/branches/${BRANCH}" --jq '.commit.sha')
printf 'status=created\nbranch=%s\nsha=%s\nurl=https://github.com/%s/tree/%s\n' \
    "${BRANCH}" "${created_sha:0:7}" "${REPO}" "${BRANCH}"
