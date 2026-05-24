#!/usr/bin/env bash
# Approve and squash-merge the onboarder PR (opened on the component repo
# by odh-konflux-onboarder.yml). Generic enough to merge any PR, but the
# only caller in this skill is the per-component sub-agent's step 5.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
onboarder-pr-merge.sh — approve and squash-merge the onboarder PR.

Required:
  --repo <owner/repo>     The PR's repo
  --pr-number <n>         The PR number

Optional:
  -h, --help              Show this help

Output (stdout, key=value lines): status (merged|already-merged|failed),
                                  merge_sha (when merged).
EOF
    exit 0
fi

REPO=""
PR_NUMBER=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)        REPO="$2";       shift 2 ;;
        --pr-number)   PR_NUMBER="$2";  shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in REPO PR_NUMBER; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

state=$(gh pr view "${PR_NUMBER}" --repo "${REPO}" --json state --jq '.state')
if [ "${state}" = "MERGED" ]; then
    sha=$(gh pr view "${PR_NUMBER}" --repo "${REPO}" --json mergeCommit --jq '.mergeCommit.oid // ""')
    printf 'status=already-merged\nmerge_sha=%s\n' "${sha:0:7}"
    exit 0
fi

# Try to approve. If the user is the PR author, GitHub will reject self-review;
# treat that as non-fatal (the merge may still succeed if branch protection
# allows it, or fail in the next step with a clear error).
gh pr review "${PR_NUMBER}" --repo "${REPO}" --approve >/dev/null 2>&1 || \
    echo "warning: pr review --approve failed (often: self-review or token scope); continuing" >&2

if ! gh pr merge "${PR_NUMBER}" --repo "${REPO}" --squash --delete-branch=false --auto=false; then
    echo "status=failed"
    exit 0
fi

sha=$(gh pr view "${PR_NUMBER}" --repo "${REPO}" --json mergeCommit --jq '.mergeCommit.oid // ""')
printf 'status=merged\nmerge_sha=%s\n' "${sha:0:7}"
