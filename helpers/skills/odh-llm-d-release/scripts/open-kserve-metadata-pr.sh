#!/usr/bin/env bash
# Open the KServe component-metadata PR.
#
# Targets opendatahub-io/kserve master (hardcoded — specific to this skill).
#
# Inputs (--updates):
#   [{"name":"llm-d-router","version":"v0.7.1"},
#    {"name":"llm-d-workload-variant-autoscaler","version":"v0.7.0"},
#    {"name":"batch-gateway","version":"v0.5.1"},
#    {"name":"llm-d-kv-cache","version":"v0.7.1"},
#    {"name":"vLLM","version":"v0.19.1"}]
#
# Behavior:
#   1. Ensure a fork of opendatahub-io/kserve exists for the current gh user.
#   2. Clone the fork into a temp dir at the master branch.
#   3. Check out a fresh branch.
#   4. For each {name, version}: update the `version:` of the matching
#      `- name: <name>` entry in <metadata_file>. If an entry does not
#      exist, append a new one with name/version/repoUrl=<best-effort>.
#   5. Commit, push to the fork, open a cross-fork PR.

set -euo pipefail

UPSTREAM_REPO="opendatahub-io/kserve"
TARGET_BRANCH="master"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<EOF
open-kserve-metadata-pr.sh — fork+edit+PR for ${UPSTREAM_REPO}.

Target: ${UPSTREAM_REPO}@${TARGET_BRANCH} (hardcoded)

Required:
  --metadata-file <path>           File to edit (e.g. config/component_metadata.yaml)
  --version <vX.Y-eaN>             ODH release version (used in branch name + PR title)
  --updates <json>                 JSON array; each entry has name + version

Optional:
  --keep <names>                   Comma-separated list of releases[] entry
                                   names to leave as-is (defaults to none)
  -h, --help                       Show this help

Output (stdout, key=value lines): status (created|exists|failed), pr_url, pr_number.
EOF
    exit 0
fi

require_value() {
    if [ "$#" -lt 2 ] || [[ "$2" == --* ]]; then
        echo "missing value for $1" >&2
        exit 2
    fi
}

METADATA_FILE=""
VERSION=""
UPDATES=""
KEEP=""

while [ $# -gt 0 ]; do
    case "$1" in
        --metadata-file) require_value "$@"; METADATA_FILE="$2"; shift 2 ;;
        --version)       require_value "$@"; VERSION="$2";       shift 2 ;;
        --updates)       require_value "$@"; UPDATES="$2";       shift 2 ;;
        --keep)          require_value "$@"; KEEP="$2";          shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

for required in METADATA_FILE VERSION UPDATES; do
    if [ -z "${!required}" ]; then
        echo "missing required arg: ${required}" >&2
        exit 2
    fi
done

# Refuse to bump a release entry whose name is in the keep list.
if [ -n "${KEEP}" ]; then
    IFS=',' read -ra keep_names <<< "${KEEP}"
    for name in "${keep_names[@]}"; do
        if printf '%s' "${UPDATES}" | jq -e --arg n "${name}" \
                'any(.[]; .name == $n)' >/dev/null; then
            echo "refusing to update kept entry: ${name}" >&2
            exit 2
        fi
    done
fi

WORKDIR=$(mktemp -d)
trap 'rm -rf "${WORKDIR}"' EXIT

gh_user=$(gh api user --jq '.login')
fork_repo="${gh_user}/${UPSTREAM_REPO##*/}"
branch_name="bump-llm-d-${VERSION}"

# Short-circuit if an open PR already exists from this fork branch — avoids a
# non-fast-forward push later when the fork has the branch from a prior run.
if existing=$(gh pr list --repo "${UPSTREAM_REPO}" \
        --head "${gh_user}:${branch_name}" \
        --state open \
        --json number,url \
        --jq '.[0]' 2>/dev/null) && [ -n "${existing}" ]; then
    pr_number=$(printf '%s' "${existing}" | jq -r '.number')
    pr_url=$(printf '%s' "${existing}" | jq -r '.url')
    printf 'status=exists\npr_number=%s\npr_url=%s\n' "${pr_number}" "${pr_url}"
    exit 0
fi

# Ensure fork exists. `gh repo fork` is idempotent — if the fork already
# exists, it just prints a notice. --clone=false avoids a duplicate clone.
# Capture the output so we can surface a real error if creation fails.
fork_output=$(gh repo fork "${UPSTREAM_REPO}" --remote=false --clone=false 2>&1) || \
    fork_output="${fork_output}  [exit non-zero, may already exist — continuing to visibility check]"

# Wait briefly for GitHub to make the fork visible.
fork_visible=false
for _ in 1 2 3 4 5; do
    if gh repo view "${fork_repo}" >/dev/null 2>&1; then
        fork_visible=true
        break
    fi
    sleep 2
done

if [ "${fork_visible}" = false ]; then
    echo "fork ${fork_repo} not visible after 10s; gh fork output was:" >&2
    echo "${fork_output}" >&2
    echo "status=failed"
    echo "reason=fork-not-visible"
    echo "fork_repo=${fork_repo}"
    exit 0
fi

# If the fork already has the branch but the open-PR short-circuit above did
# not match, the branch is orphaned (PR was previously closed or merged).
# Pushing a fresh branch over it would fail non-fast-forward; we don't
# overwrite human-touched state automatically.
if gh api "repos/${fork_repo}/branches/${branch_name}" --jq '.name' >/dev/null 2>&1; then
    cat <<EOF >&2

Branch \`${branch_name}\` already exists on your fork (${fork_repo}) but no open
PR is associated with it (it was likely closed or merged in a previous run).
A non-fast-forward push would overwrite work. Please resolve manually, then
re-run:

  # Option A — delete the stale branch on your fork:
  gh api -X DELETE repos/${fork_repo}/git/refs/heads/${branch_name}

  # Option B — reopen the previous PR if it was closed by mistake:
  gh pr list --repo ${UPSTREAM_REPO} --head ${gh_user}:${branch_name} --state closed

EOF
    echo "status=failed"
    echo "reason=stale-branch-on-fork"
    echo "fork_repo=${fork_repo}"
    echo "branch=${branch_name}"
    exit 0
fi

git -C "${WORKDIR}" clone --depth=1 --branch "${TARGET_BRANCH}" \
    "https://github.com/${UPSTREAM_REPO}.git" repo
cd "${WORKDIR}/repo"
git remote add fork "https://github.com/${fork_repo}.git"
git checkout -b "${branch_name}"

if [ ! -f "${METADATA_FILE}" ]; then
    echo "metadata file not found in repo: ${METADATA_FILE}" >&2
    exit 1
fi

# Apply each update. Pass name/version to yq via environment variables and
# strenv() so a stray `"` or yq metacharacter in the input can't change the
# filter (defense against malformed --updates JSON).
count=$(printf '%s' "${UPDATES}" | jq 'length')
for i in $(seq 0 $((count - 1))); do
    entry=$(printf '%s' "${UPDATES}" | jq ".[${i}]")
    name=$(printf '%s' "${entry}" | jq -r '.name')
    version=$(printf '%s' "${entry}" | jq -r '.version')

    export YQ_NAME="${name}" YQ_VERSION="${version}"
    if yq -e '(.releases[] | select(.name == strenv(YQ_NAME)))' "${METADATA_FILE}" >/dev/null 2>&1; then
        yq -i '(.releases[] | select(.name == strenv(YQ_NAME)) | .version) = strenv(YQ_VERSION)' \
            "${METADATA_FILE}"
    else
        # New entry — best-effort repoUrl, leaves user to refine in the PR.
        yq -i '.releases += [{"name": strenv(YQ_NAME), "version": strenv(YQ_VERSION), "repoUrl": "https://github.com/llm-d"}]' \
            "${METADATA_FILE}"
    fi
done
unset YQ_NAME YQ_VERSION

if git diff --quiet -- "${METADATA_FILE}"; then
    echo "status=failed"
    echo "reason=no-changes"
    exit 0
fi

git config user.email "${gh_user}@users.noreply.github.com"
git config user.name "${gh_user}"
git add "${METADATA_FILE}"
git commit -m "bump llm-d component versions for ODH ${VERSION}"
git push -u fork "${branch_name}"

pr_title="Bump llm-d component versions for ODH ${VERSION}"
# shellcheck disable=SC2016  # backticks are markdown, not shell command substitution
pr_body=$(printf 'Updates `%s` with the upstream versions used in ODH release %s.\n' \
    "${METADATA_FILE}" "${VERSION}")

if ! gh pr create --repo "${UPSTREAM_REPO}" \
        --base "${TARGET_BRANCH}" \
        --head "${gh_user}:${branch_name}" \
        --title "${pr_title}" \
        --body "${pr_body}" \
        >/dev/null; then
    echo "status=failed"
    exit 0
fi

pr_info=$(gh pr list --repo "${UPSTREAM_REPO}" \
    --head "${gh_user}:${branch_name}" \
    --state open \
    --json number,url \
    --jq '.[0]')
pr_number=$(printf '%s' "${pr_info}" | jq -r '.number')
pr_url=$(printf '%s' "${pr_info}" | jq -r '.url')
printf 'status=created\npr_number=%s\npr_url=%s\n' "${pr_number}" "${pr_url}"
