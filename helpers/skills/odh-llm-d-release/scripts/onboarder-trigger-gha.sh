#!/usr/bin/env bash
# Trigger odh-konflux-onboarder.yml on opendatahub-io/odh-konflux-central with
# build_type=Release.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
onboarder-trigger-gha.sh — trigger odh-konflux-onboarder.yml for one component.

Required:
  --component <name>            Dropdown value (e.g. llm-d-inference-scheduler)
  --pr-target-branch <name>     Release branch (e.g. release-v3.5-ea2)
  --version <vX.Y-eaN>          ODH version (e.g. v3.5-ea2); becomes the
                                Konflux image tag

Optional:
  --konflux-central <owner/repo>  Defaults to opendatahub-io/odh-konflux-central
  --workflow <file.yml>           Defaults to odh-konflux-onboarder.yml
  -h, --help                      Show this help

Output (stdout, key=value lines): status (triggered), run_id, run_url.
EOF
    exit 0
fi

COMPONENT=""
PR_TARGET_BRANCH=""
VERSION=""
KONFLUX_CENTRAL="opendatahub-io/odh-konflux-central"
WORKFLOW="odh-konflux-onboarder.yml"

while [ $# -gt 0 ]; do
    case "$1" in
        --component)         COMPONENT="$2";         shift 2 ;;
        --pr-target-branch)  PR_TARGET_BRANCH="$2";  shift 2 ;;
        --version)           VERSION="$2";           shift 2 ;;
        --konflux-central)   KONFLUX_CENTRAL="$2";   shift 2 ;;
        --workflow)          WORKFLOW="$2";          shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in COMPONENT PR_TARGET_BRANCH VERSION; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

# Workflow inputs per odh-konflux-onboarder.yml:
#   component, pr_target_branch, build_type=Release, version, build_branch
# build_branch defaults to pr_target_branch inside the workflow.
gh workflow run "${WORKFLOW}" \
    --repo "${KONFLUX_CENTRAL}" \
    --ref main \
    -f "component=${COMPONENT}" \
    -f "pr_target_branch=${PR_TARGET_BRANCH}" \
    -f "build_type=Release" \
    -f "version=${VERSION}"

# Runs queue asynchronously; try briefly to surface the run we just kicked.
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
