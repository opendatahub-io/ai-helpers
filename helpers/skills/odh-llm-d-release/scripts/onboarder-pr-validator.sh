#!/usr/bin/env bash
# Validate the content of the PR opened by odh-konflux-onboarder.yml against
# the per-image expectations in components.yaml. For each expected tekton
# file, check that the file is in the PR and that its params match
# (output-image, path-context, dockerfile, on-cel-expression target_branch).
#
# Designed to be called once per component (with that component's expected
# konflux_files passed as a JSON array via --expected-json).

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
onboarder-pr-validator.sh — verify onboarder PR matches expected content.

Required:
  --component-repo <owner/repo>     ODH component repo
  --pr-number <n>                   PR number opened by the onboarder
  --release-branch <name>           Expected target_branch in on-cel-expression
  --version <vX.Y-eaN>              Expected image tag in output-image
  --quay-org <name>                 Quay org for output-image (e.g. opendatahub)
  --expected-json <json>            JSON array; each element has:
                                      tekton_file, quay_image, dockerfile, path_context

Optional:
  -h, --help                        Show this help

Output (stdout, key=value lines):
  status=ok|fail
  problems_count=<n>
  problems=<json>     (when fail; an array of {file, field, expected, actual})
Always exits 0; status carries the verdict.
EOF
    exit 0
fi

COMPONENT_REPO=""
PR_NUMBER=""
RELEASE_BRANCH=""
VERSION=""
QUAY_ORG=""
EXPECTED_JSON=""

while [ $# -gt 0 ]; do
    case "$1" in
        --component-repo)  COMPONENT_REPO="$2";  shift 2 ;;
        --pr-number)       PR_NUMBER="$2";       shift 2 ;;
        --release-branch)  RELEASE_BRANCH="$2";  shift 2 ;;
        --version)         VERSION="$2";         shift 2 ;;
        --quay-org)        QUAY_ORG="$2";        shift 2 ;;
        --expected-json)   EXPECTED_JSON="$2";   shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in COMPONENT_REPO PR_NUMBER RELEASE_BRANCH VERSION QUAY_ORG EXPECTED_JSON; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

WORKDIR=$(mktemp -d)
trap 'rm -rf "${WORKDIR}"' EXIT

# Pull the PR's head ref so we can read the actual files (vs reading the diff).
gh pr view "${PR_NUMBER}" --repo "${COMPONENT_REPO}" \
    --json headRepository,headRefOid,files \
    > "${WORKDIR}/pr.json"

head_sha=$(jq -r '.headRefOid' "${WORKDIR}/pr.json")
head_repo=$(jq -r '.headRepository.nameWithOwner // empty' "${WORKDIR}/pr.json")
if [ -z "${head_repo}" ]; then
    head_repo="${COMPONENT_REPO}"
fi

problems="[]"

add_problem() {
    local file="$1" field="$2" expected="$3" actual="$4"
    problems=$(printf '%s' "${problems}" \
        | jq --arg f "${file}" --arg fld "${field}" --arg e "${expected}" --arg a "${actual}" \
             '. + [{file: $f, field: $fld, expected: $e, actual: $a}]')
}

fetch_file() {
    # Fetch a file's content at the PR head into the workdir; returns 0 if found.
    local path="$1"
    local out="$2"
    gh api "repos/${head_repo}/contents/${path}?ref=${head_sha}" \
        --jq '.content' 2>/dev/null \
        | base64 -d > "${out}" 2>/dev/null \
        && [ -s "${out}" ]
}

count=$(printf '%s' "${EXPECTED_JSON}" | jq 'length')
for i in $(seq 0 $((count - 1))); do
    entry=$(printf '%s' "${EXPECTED_JSON}" | jq ".[${i}]")
    tekton_file=$(printf '%s' "${entry}" | jq -r '.tekton_file')
    quay_image=$(printf '%s' "${entry}" | jq -r '.quay_image')
    dockerfile=$(printf '%s' "${entry}" | jq -r '.dockerfile')
    path_context=$(printf '%s' "${entry}" | jq -r '.path_context')

    local_file="${WORKDIR}/$(basename "${tekton_file}")"
    if ! fetch_file "${tekton_file}" "${local_file}"; then
        add_problem "${tekton_file}" "existence" "present in PR" "missing"
        continue
    fi

    # on-cel-expression should reference the release branch as target_branch.
    cel=$(yq -r '.metadata.annotations."pipelinesascode.tekton.dev/on-cel-expression" // ""' "${local_file}")
    if ! printf '%s' "${cel}" | grep -qE "target_branch[[:space:]]*==[[:space:]]*\"${RELEASE_BRANCH}\""; then
        add_problem "${tekton_file}" "on-cel-expression.target_branch" \
            "target_branch == \"${RELEASE_BRANCH}\"" \
            "${cel}"
    fi

    # spec.params lookups (PipelineRun structure: spec.params[*].name/value).
    expected_image="quay.io/${QUAY_ORG}/${quay_image}:${VERSION}"
    actual_image=$(yq -r '(.spec.params[] | select(.name == "output-image") | .value) // ""' "${local_file}")
    if [ "${actual_image}" != "${expected_image}" ]; then
        add_problem "${tekton_file}" "spec.params.output-image" \
            "${expected_image}" "${actual_image}"
    fi

    actual_path=$(yq -r '(.spec.params[] | select(.name == "path-context") | .value) // ""' "${local_file}")
    # Normalize trailing slash so "." and "./" are treated as equivalent.
    norm_actual="${actual_path%/}"
    norm_expected="${path_context%/}"
    if [ "${norm_actual}" != "${norm_expected}" ]; then
        add_problem "${tekton_file}" "spec.params.path-context" \
            "${path_context}" "${actual_path}"
    fi

    actual_dockerfile=$(yq -r '(.spec.params[] | select(.name == "dockerfile") | .value) // ""' "${local_file}")
    if [ "${actual_dockerfile}" != "${dockerfile}" ]; then
        add_problem "${tekton_file}" "spec.params.dockerfile" \
            "${dockerfile}" "${actual_dockerfile}"
    fi
done

problems_count=$(printf '%s' "${problems}" | jq 'length')
if [ "${problems_count}" -eq 0 ]; then
    echo "status=ok"
    echo "problems_count=0"
else
    echo "status=fail"
    echo "problems_count=${problems_count}"
    echo "problems=${problems}"
fi
