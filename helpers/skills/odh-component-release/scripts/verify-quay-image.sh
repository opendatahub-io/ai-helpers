#!/usr/bin/env bash
# Verify that a tagged image exists in quay.io/<org>/<image>:<tag>.
# Optionally polls with a bounded timeout (builds are async).
#
# Usage:
#   verify-quay-image.sh --org <org> --image <image> --tag <tag> \
#                        [--wait-seconds <N>] [--poll-interval <S>]
#
# Output (stdout, one key=value per line):
#   status=found|missing
#   ref=quay.io/<org>/<image>:<tag>
#   browse_url=https://quay.io/repository/<org>/<image>?tab=tags
#   digest=<sha256:...>   (when found)
#
# Exit codes: 0 always (status field carries the verdict).

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
verify-quay-image.sh — check whether a tag exists at quay.io/<org>/<image>:<tag>.

Required:
  --org <name>           Quay org (e.g. opendatahub)
  --image <name>         Image short name
  --tag <name>           Tag to look for (e.g. v0.5.0)

Optional:
  --wait-seconds <N>     Poll for up to N seconds (default 0 = single probe)
  --poll-interval <S>    Seconds between probes (default 15)
  -h, --help             Show this help

Output (stdout, key=value lines): status (found|missing), ref, browse_url, digest.
Always exits 0; the status field carries the verdict.
EOF
    exit 0
fi

ORG=""
IMAGE=""
TAG=""
WAIT_SECONDS=0
POLL_INTERVAL=15

while [ $# -gt 0 ]; do
    case "$1" in
        --org)            ORG="$2";            shift 2 ;;
        --image)          IMAGE="$2";          shift 2 ;;
        --tag)            TAG="$2";            shift 2 ;;
        --wait-seconds)   WAIT_SECONDS="$2";   shift 2 ;;
        --poll-interval)  POLL_INTERVAL="$2";  shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in ORG IMAGE TAG; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

REF="quay.io/${ORG}/${IMAGE}:${TAG}"
BROWSE_URL="https://quay.io/repository/${ORG}/${IMAGE}?tab=tags"

probe() {
    # Returns 0 + prints digest on stdout if tag exists, non-zero otherwise.
    skopeo inspect --no-tags "docker://${REF}" 2>/dev/null \
        | jq -r '.Digest // empty'
}

deadline=$(( $(date +%s) + WAIT_SECONDS ))
while :; do
    digest=$(probe || true)
    if [ -n "${digest:-}" ]; then
        printf 'status=found\nref=%s\nbrowse_url=%s\ndigest=%s\n' \
            "${REF}" "${BROWSE_URL}" "${digest}"
        exit 0
    fi
    if [ "$(date +%s)" -ge "${deadline}" ]; then
        printf 'status=missing\nref=%s\nbrowse_url=%s\n' "${REF}" "${BROWSE_URL}"
        exit 0
    fi
    sleep "${POLL_INTERVAL}"
done
