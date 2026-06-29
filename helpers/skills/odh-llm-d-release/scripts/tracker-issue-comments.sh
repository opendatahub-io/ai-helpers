#!/usr/bin/env bash
# Post the final #Release# comment on the ODH release tracker issue.

set -euo pipefail

REPO="opendatahub-io/opendatahub-community"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<EOF
tracker-issue-comments.sh — post the #Release# comment on the tracker issue.

Target: ${REPO} (hardcoded)

Required:
  --issue-number <n>       Tracker issue number
  --body-file <path>       File containing the prepared comment body

Optional:
  -h, --help               Show this help

Output (stdout, key=value lines): status (posted|failed), comment_url.
EOF
    exit 0
fi

require_value() {
    if [ "$#" -lt 2 ] || [[ "$2" == --* ]]; then
        echo "missing value for $1" >&2
        exit 2
    fi
}

ISSUE_NUMBER=""
BODY_FILE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --issue-number) require_value "$@"; ISSUE_NUMBER="$2"; shift 2 ;;
        --body-file)    require_value "$@"; BODY_FILE="$2";    shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in ISSUE_NUMBER BODY_FILE; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

if ! [[ "${ISSUE_NUMBER}" =~ ^[1-9][0-9]*$ ]]; then
    echo "--issue-number must be a positive integer, got: ${ISSUE_NUMBER}" >&2
    exit 2
fi

if [ ! -f "${BODY_FILE}" ]; then
    echo "body file not found: ${BODY_FILE}" >&2
    exit 2
fi

if ! comment_url=$(gh issue comment "${ISSUE_NUMBER}" \
        --repo "${REPO}" \
        --body-file "${BODY_FILE}"); then
    echo "status=failed"
    exit 0
fi

printf 'status=posted\ncomment_url=%s\n' "${comment_url}"
