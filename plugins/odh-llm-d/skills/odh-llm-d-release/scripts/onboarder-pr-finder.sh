#!/usr/bin/env bash
# Locate the PR the Konflux onboarder workflow opened against the release
# branch. The onboarder runs asynchronously, so this supports bounded polling.
#
# Hardening: rejects cross-fork PRs (only same-repo PRs are eligible) and
# sorts by createdAt desc so newest wins deterministically. If you know the
# onboarder's bot author login, pass --expected-author to require an exact
# match.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
onboarder-pr-finder.sh — find the PR opened by odh-konflux-onboarder.yml.

Required:
  --component-repo <owner/repo>    ODH component repo (e.g. opendatahub-io/batch-gateway)
  --release-branch <name>          PR target branch (e.g. release-v3.5-ea2)

Optional:
  --expected-author <login>        If set, only consider PRs authored by this
                                   login (e.g. "odh-devops-app[bot]" for
                                   the ODH DevOps GitHub App). Defends
                                   against arbitrary users opening a PR to
                                   the release branch and being picked as
                                   the onboarder PR.
  --timeout <N>          Poll up to N seconds for the PR to appear (default 900 = 15 min)
  --poll-interval <S>    Seconds between probes (default 60 = 1 min)
  -h, --help             Show this help

Output (stdout, key=value lines):
  status (found|missing), pr_number, pr_url, pr_title, head_ref, head_sha, author
Always exits 0; the status field carries the verdict.

Selection logic:
  1. Open PRs targeting --release-branch in --component-repo.
  2. Reject any PR whose head is in a different repo (no cross-fork PRs).
  3. If --expected-author is set, require an exact author.login match.
  4. Sort remaining by createdAt desc, return the newest.
EOF
    exit 0
fi

require_value() {
    if [ "$#" -lt 2 ] || [[ "$2" == --* ]]; then
        echo "missing value for $1" >&2
        exit 2
    fi
}

require_positive_int() {
    local name="$1" value="$2"
    if ! [[ "${value}" =~ ^[0-9]+$ ]] || [ "${value}" -lt 0 ]; then
        echo "${name} must be a non-negative integer, got: ${value}" >&2
        exit 2
    fi
}

COMPONENT_REPO=""
RELEASE_BRANCH=""
EXPECTED_AUTHOR=""
TIMEOUT=900
POLL_INTERVAL=60

while [ $# -gt 0 ]; do
    case "$1" in
        --component-repo)  require_value "$@"; COMPONENT_REPO="$2";  shift 2 ;;
        --release-branch)  require_value "$@"; RELEASE_BRANCH="$2";  shift 2 ;;
        --expected-author) require_value "$@"; EXPECTED_AUTHOR="$2"; shift 2 ;;
        --timeout)         require_value "$@"; TIMEOUT="$2";         shift 2 ;;
        --poll-interval)   require_value "$@"; POLL_INTERVAL="$2";   shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in COMPONENT_REPO RELEASE_BRANCH; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

require_positive_int "--timeout" "${TIMEOUT}"
require_positive_int "--poll-interval" "${POLL_INTERVAL}"

probe() {
    # Filter rules:
    #   - same-repo only (isCrossRepository == false) → rules out forks
    #   - optional exact author match
    #   - newest createdAt wins (deterministic)
    gh pr list \
        --repo "${COMPONENT_REPO}" \
        --base "${RELEASE_BRANCH}" \
        --state open \
        --limit 20 \
        --json number,title,url,state,headRefName,headRefOid,author,createdAt,isCrossRepository \
        2>/dev/null \
        | jq -r --arg expected_author "${EXPECTED_AUTHOR}" '
            map(select(.isCrossRepository == false))
            | (if $expected_author == "" then .
               else map(select(.author.login == $expected_author)) end)
            | sort_by(.createdAt) | reverse
            | .[0] // empty
          '
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
head_sha=$(printf '%s' "${match}" | jq -r '.headRefOid')
author=$(printf '%s' "${match}" | jq -r '.author.login')

printf 'status=found\npr_number=%s\npr_url=%s\npr_title=%s\nhead_ref=%s\nhead_sha=%s\nauthor=%s\n' \
    "${pr_number}" "${pr_url}" "${pr_title}" "${head_ref}" "${head_sha}" "${author}"
