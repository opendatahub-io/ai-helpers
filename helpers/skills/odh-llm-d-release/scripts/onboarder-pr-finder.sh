#!/usr/bin/env bash
# Locate the PR the Konflux onboarder workflow opened against the release
# branch. The onboarder runs asynchronously, so this supports bounded polling.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
onboarder-pr-finder.sh — find the PR opened by odh-konflux-onboarder.yml.

Required:
  --component-repo <owner/repo>    ODH component repo (e.g. opendatahub-io/batch-gateway)
  --release-branch <name>          PR target branch (e.g. release-v3.5-ea2)

Optional:
  --timeout <N>          Poll up to N seconds for the PR to appear (default 900 = 15 min)
  --poll-interval <S>    Seconds between probes (default 60 = 1 min)
  -h, --help             Show this help

Output (stdout, key=value lines):
  status (found|missing), pr_number, pr_url, pr_title, head_ref
Always exits 0; the status field carries the verdict.
EOF
    exit 0
fi

COMPONENT_REPO=""
RELEASE_BRANCH=""
TIMEOUT=900
POLL_INTERVAL=60

while [ $# -gt 0 ]; do
    case "$1" in
        --component-repo)  COMPONENT_REPO="$2";  shift 2 ;;
        --release-branch)  RELEASE_BRANCH="$2";  shift 2 ;;
        --timeout)         TIMEOUT="$2";         shift 2 ;;
        --poll-interval)   POLL_INTERVAL="$2";   shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in COMPONENT_REPO RELEASE_BRANCH; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

probe() {
    # Return the newest OPEN PR targeting RELEASE_BRANCH. The onboarder PR is
    # the only thing that should open against this branch right after the
    # release branch is created, so we don't need title-based filtering.
    gh pr list \
        --repo "${COMPONENT_REPO}" \
        --base "${RELEASE_BRANCH}" \
        --state open \
        --limit 5 \
        --json number,title,url,state,headRefName \
        2>/dev/null \
        | jq -r '.[0] // empty'
}

deadline=$(( $(date +%s) + TIMEOUT ))
match=""
while :; do
    match=$(probe || true)
    if [ -n "${match}" ]; then
        break
    fi
    if [ "$(date +%s)" -ge "${deadline}" ]; then
        echo "status=missing"
        exit 0
    fi
    sleep "${POLL_INTERVAL}"
done

pr_number=$(printf '%s' "${match}" | jq -r '.number')
pr_url=$(printf '%s' "${match}" | jq -r '.url')
pr_title=$(printf '%s' "${match}" | jq -r '.title')
head_ref=$(printf '%s' "${match}" | jq -r '.headRefName')

printf 'status=found\npr_number=%s\npr_url=%s\npr_title=%s\nhead_ref=%s\n' \
    "${pr_number}" "${pr_url}" "${pr_title}" "${head_ref}"
