#!/usr/bin/env bash
# Verify that the Konflux release onboarder produced its expected artifact:
# a PR opened on the ODH component repo against the release branch, adding
# the .tekton/ pipeline files for the new Konflux component.
#
# Usage:
#   verify-konflux-pr.sh --component-repo <owner/repo> --release-branch <branch> \
#                        --konflux-component <name>
#
# Output (stdout, one key=value per line):
#   status=found|missing
#   pr_number=<n>     (when found)
#   pr_url=<url>      (when found)
#   pr_state=<state>  (when found: OPEN | MERGED | CLOSED)
#
# Exit codes: 0 always (status field carries the verdict).

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
verify-konflux-pr.sh — find the PR the Konflux onboarder opened against the
release branch for one Konflux sub-component.

Required:
  --component-repo <owner/repo>    ODH component repo (e.g. opendatahub-io/batch-gateway)
  --release-branch <name>          e.g. release-v0.5.0
  --konflux-component <name>       Sub-component to look for (e.g. batch-gateway-apiserver)

  -h, --help                       Show this help

Output (stdout, key=value lines): status (found|missing), pr_number, pr_url, pr_state.
Always exits 0; the status field carries the verdict.
EOF
    exit 0
fi

COMPONENT_REPO=""
RELEASE_BRANCH=""
KONFLUX_COMPONENT=""

while [ $# -gt 0 ]; do
    case "$1" in
        --component-repo)    COMPONENT_REPO="$2";    shift 2 ;;
        --release-branch)    RELEASE_BRANCH="$2";    shift 2 ;;
        --konflux-component) KONFLUX_COMPONENT="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in COMPONENT_REPO RELEASE_BRANCH KONFLUX_COMPONENT; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

# Search recent PRs (open or merged) targeting the release branch. The
# onboarder typically titles its PR with the Konflux component name; we
# filter by title substring as a heuristic.
prs_json=$(gh pr list \
    --repo "${COMPONENT_REPO}" \
    --base "${RELEASE_BRANCH}" \
    --state all \
    --limit 30 \
    --json number,title,url,state,headRefName)

match=$(printf '%s' "${prs_json}" | jq -r --arg c "${KONFLUX_COMPONENT}" '
    [.[] | select((.title | ascii_downcase | contains($c | ascii_downcase))
              or (.headRefName | ascii_downcase | contains($c | ascii_downcase)))]
    | .[0] // empty
')

if [ -z "${match}" ]; then
    echo "status=missing"
    exit 0
fi

pr_number=$(printf '%s' "${match}" | jq -r '.number')
pr_url=$(printf '%s' "${match}" | jq -r '.url')
pr_state=$(printf '%s' "${match}" | jq -r '.state')

printf 'status=found\npr_number=%s\npr_url=%s\npr_state=%s\n' \
    "${pr_number}" "${pr_url}" "${pr_state}"
