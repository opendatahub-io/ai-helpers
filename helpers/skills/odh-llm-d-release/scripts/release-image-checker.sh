#!/usr/bin/env bash
# Verify that a tagged image exists in quay.io/<org>/<image>:<tag>.
# Polls Quay's public REST API with a bounded timeout. No auth needed for
# public repos (e.g. quay.io/opendatahub).

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
release-image-checker.sh — check whether a tag exists at quay.io/<org>/<image>:<tag>.

Required:
  --org <name>           Quay org (e.g. opendatahub)
  --image <name>         Image short name
  --tag <name>           Tag (e.g. v3.5-ea2)

Optional:
  --timeout <N>          Poll up to N seconds (default 900 = 15 min)
  --poll-interval <S>    Seconds between probes (default 60 = 1 min)
  -h, --help             Show this help

Output (stdout, key=value lines): status (found|missing), ref, browse_url, digest.
Always exits 0; status carries the verdict.
EOF
    exit 0
fi

ORG=""
IMAGE=""
TAG=""
TIMEOUT=900
POLL_INTERVAL=60

while [ $# -gt 0 ]; do
    case "$1" in
        --org)            ORG="$2";            shift 2 ;;
        --image)          IMAGE="$2";          shift 2 ;;
        --tag)            TAG="$2";            shift 2 ;;
        --timeout)        TIMEOUT="$2";        shift 2 ;;
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

API_URL="https://quay.io/api/v1/repository/${ORG}/${IMAGE}/tag/?specificTag=${TAG}"

probe() {
    # Quay returns {"tags":[{...,"manifest_digest":"sha256:..."}]} when the tag
    # exists, or an empty "tags" array when it doesn't. 404 means the repo
    # itself is missing.
    curl -fsS --max-time 10 "${API_URL}" 2>/dev/null \
        | jq -r '.tags[0].manifest_digest // empty'
}

deadline=$(( $(date +%s) + TIMEOUT ))
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
