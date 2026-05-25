#!/usr/bin/env bash
# Create a draft GitHub release with auto-generated notes on a component repo.
# Idempotent: if the release tag already exists, reports "exists" and exits 0.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
create-github-release.sh — create a draft release with --generate-notes.

Required:
  --repo <owner/repo>      Component repo
  --tag <name>             Release tag (e.g. odh-v3.5-ea2)
  --target-branch <name>   Branch the tag points to (e.g. release-v3.5-ea2)

Optional:
  --title <text>           Release title (defaults to the tag value)
  -h, --help               Show this help

Output (stdout, key=value lines): status (created|exists|failed),
                                  tag, release_url.
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
TAG=""
TARGET_BRANCH=""
TITLE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)          require_value "$@"; REPO="$2";          shift 2 ;;
        --tag)           require_value "$@"; TAG="$2";           shift 2 ;;
        --target-branch) require_value "$@"; TARGET_BRANCH="$2"; shift 2 ;;
        --title)         require_value "$@"; TITLE="$2";         shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in REPO TAG TARGET_BRANCH; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

if [ -z "${TITLE}" ]; then
    TITLE="${TAG}"
fi

# Idempotency: if the release already exists for this tag, return existing URL.
if existing_url=$(gh release view "${TAG}" --repo "${REPO}" --json url --jq '.url' 2>/dev/null); then
    if [ -n "${existing_url}" ]; then
        printf 'status=exists\ntag=%s\nrelease_url=%s\n' "${TAG}" "${existing_url}"
        exit 0
    fi
fi

if ! gh release create "${TAG}" \
        --repo "${REPO}" \
        --target "${TARGET_BRANCH}" \
        --title "${TITLE}" \
        --generate-notes \
        --draft \
        >/dev/null; then
    echo "status=failed"
    exit 0
fi

release_url=$(gh release view "${TAG}" --repo "${REPO}" --json url --jq '.url')
printf 'status=created\ntag=%s\nrelease_url=%s\n' "${TAG}" "${release_url}"
echo "NOTE: release ${TAG} is a draft — mark it official once ready to publish: ${release_url}" >&2
