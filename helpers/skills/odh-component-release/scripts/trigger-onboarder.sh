#!/usr/bin/env bash
# Trigger the odh-konflux-release-onboarder workflow on opendatahub-io/odh-konflux-central
# for one Konflux component.
#
# Mirrors the manual inputs documented in onboarding-component.md:
#   repository_name = <konflux-component-name>   (dropdown in workflow UI)
#   branch          = <release-vX.Y.Z>           (branch to open PR against)
#   image_branch    = <release-vX.Y.Z>           (branch images built from, same)
#   release_type    = Release
#   version         = <vX.Y.Z>                   (image tag)
#
# Usage:
#   trigger-onboarder.sh --konflux-central <owner/repo> --workflow <file.yml> \
#                        --component <name> --release-branch <branch> \
#                        --version <vX.Y.Z> [--dry-run]
#
# Output (stdout, one key=value per line):
#   status=triggered|would-trigger
#   run_id=<id>           (only when status=triggered; may be empty briefly)
#   run_url=<url>         (only when status=triggered; may be empty briefly)

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
trigger-onboarder.sh — trigger odh-konflux-release-onboarder.yml for one
Konflux sub-component.

Required:
  --konflux-central <owner/repo>   e.g. opendatahub-io/odh-konflux-central
  --workflow <file.yml>            e.g. odh-konflux-release-onboarder.yml
  --component <name>               Konflux dropdown name (e.g. batch-gateway-apiserver)
  --release-branch <name>          e.g. release-v0.5.0
  --version <vX.Y.Z>               Image tag (e.g. v0.5.0)

Optional:
  --dry-run                        Print what would run; do not invoke
  -h, --help                       Show this help

Output (stdout, key=value lines): status, run_id, run_url.
EOF
    exit 0
fi

KONFLUX_CENTRAL=""
WORKFLOW=""
COMPONENT=""
RELEASE_BRANCH=""
VERSION=""
DRY_RUN="false"

while [ $# -gt 0 ]; do
    case "$1" in
        --konflux-central) KONFLUX_CENTRAL="$2"; shift 2 ;;
        --workflow)        WORKFLOW="$2";        shift 2 ;;
        --component)       COMPONENT="$2";       shift 2 ;;
        --release-branch)  RELEASE_BRANCH="$2";  shift 2 ;;
        --version)         VERSION="$2";         shift 2 ;;
        --dry-run)         DRY_RUN="true";       shift ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in KONFLUX_CENTRAL WORKFLOW COMPONENT RELEASE_BRANCH VERSION; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

if [ "${DRY_RUN}" = "true" ]; then
    echo "status=would-trigger"
    exit 0
fi

# gh workflow run accepts -f key=value pairs that map to workflow_dispatch inputs.
gh workflow run "${WORKFLOW}" \
    --repo "${KONFLUX_CENTRAL}" \
    --ref main \
    -f "repository_name=${COMPONENT}" \
    -f "branch=${RELEASE_BRANCH}" \
    -f "image_branch=${RELEASE_BRANCH}" \
    -f "release_type=Release" \
    -f "version=${VERSION}"

# Workflow runs are queued asynchronously. Try once to find the newest run for
# this workflow; the caller can re-query later if the run hasn't appeared yet.
run_id=""
run_url=""
for _ in 1 2 3 4 5; do
    sleep 2
    run_json=$(gh run list \
        --repo "${KONFLUX_CENTRAL}" \
        --workflow "${WORKFLOW}" \
        --limit 1 \
        --json databaseId,url 2>/dev/null || echo "[]")
    run_id=$(printf '%s' "${run_json}" | jq -r '.[0].databaseId // empty')
    run_url=$(printf '%s' "${run_json}" | jq -r '.[0].url // empty')
    if [ -n "${run_id}" ]; then
        break
    fi
done

printf 'status=triggered\nrun_id=%s\nrun_url=%s\n' "${run_id}" "${run_url}"
