#!/usr/bin/env bash
# Approve and squash-merge the onboarder PR (opened on the component repo
# by odh-konflux-onboarder.yml). Generic enough to merge any PR, but the
# only caller in this skill is the per-component sub-agent's step 5.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
onboarder-pr-merge.sh — approve and squash-merge the onboarder PR.

Required:
  --repo <owner/repo>      The PR's repo
  --pr-number <n>          The PR number

Optional:
  --expected-head-sha <sha> If set, merge only if the PR's head SHA still
                            matches (prevents TOCTOU between validation and
                            merge). Passed to gh as --match-head-commit.
  -h, --help               Show this help

Output (stdout, key=value lines): status (merged|already-merged|failed|head-moved),
                                  merge_sha (when merged).
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
PR_NUMBER=""
EXPECTED_HEAD_SHA=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)              require_value "$@"; REPO="$2";              shift 2 ;;
        --pr-number)         require_value "$@"; PR_NUMBER="$2";         shift 2 ;;
        --expected-head-sha) require_value "$@"; EXPECTED_HEAD_SHA="$2"; shift 2 ;;
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

# If caller pinned an expected head SHA, fail fast when the PR head moved
# between validation and now. This is the TOCTOU defense (CWE-367) — even
# though our threat model considers unauthorized writes to the source branch
# unlikely, the pin costs nothing and turns silent races into clear failures.
if [ -n "${EXPECTED_HEAD_SHA}" ]; then
    current_head=$(gh pr view "${PR_NUMBER}" --repo "${REPO}" --json headRefOid --jq '.headRefOid')
    if [ "${current_head}" != "${EXPECTED_HEAD_SHA}" ]; then
        printf 'status=head-moved\nexpected_head=%s\ncurrent_head=%s\n' \
            "${EXPECTED_HEAD_SHA}" "${current_head}"
        exit 0
    fi
fi

# Try to approve. If the user is the PR author, GitHub will reject self-review;
# treat that as non-fatal (the merge may still succeed if branch protection
# allows it, or fail in the next step with a clear error).
gh pr review "${PR_NUMBER}" --repo "${REPO}" --approve >/dev/null 2>&1 || \
    echo "warning: pr review --approve failed (often: self-review or token scope); continuing" >&2

merge_args=(--squash --delete-branch=false --auto=false)
if [ -n "${EXPECTED_HEAD_SHA}" ]; then
    merge_args+=(--match-head-commit "${EXPECTED_HEAD_SHA}")
fi

if ! gh pr merge "${PR_NUMBER}" --repo "${REPO}" "${merge_args[@]}"; then
    echo "status=failed"
    exit 0
fi

sha=$(gh pr view "${PR_NUMBER}" --repo "${REPO}" --json mergeCommit --jq '.mergeCommit.oid // ""')
printf 'status=merged\nmerge_sha=%s\n' "${sha:0:7}"
