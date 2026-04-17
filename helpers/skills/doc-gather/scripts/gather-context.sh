#!/usr/bin/env bash
# Clone or fetch repos at specified branches and list candidate files.
#
# Usage:
#   bash gather-context.sh <repo-slug> <branch> [path-pattern...]
#
# Examples:
#   bash gather-context.sh opendatahub-io/opendatahub-documentation main "modules/**/*.adoc" "assemblies/**/*.adoc"
#   bash gather-context.sh red-hat-data-services/rhods-operator main "api/**/*_types.go"
#
# Output (JSON to stdout):
# {
#   "repo": "opendatahub-io/opendatahub-documentation",
#   "branch": "main",
#   "clone_path": "workspace/repos/opendatahub-io/opendatahub-documentation",
#   "candidates": [
#     {
#       "file_path": "modules/serving/pages/con_model-serving.adoc",
#       "size_bytes": 4521,
#       "source_type": "documentation"
#     }
#   ]
# }

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load shared git utilities (also loads .env via load-env.sh)
source "${SCRIPTS_DIR}/git-utils.sh"

REPO_SLUG="${1:?Usage: gather-context.sh <repo-slug> <branch> [path-pattern...]}"
BRANCH="${2:?Usage: gather-context.sh <repo-slug> <branch> [path-pattern...]}"
shift 2
PATH_PATTERNS=("$@")

# Clone or fetch using shared utility
CLONE_DIR=$(git_clone_or_fetch "$REPO_SLUG" "$BRANCH" 2>/dev/null) || {
    echo "Error: failed to clone ${REPO_SLUG} at branch ${BRANCH}" >&2
    jq -n --arg repo "$REPO_SLUG" --arg branch "$BRANCH" --arg path "${WORKSPACE}/${REPO_SLUG}" \
        '{repo: $repo, branch: $branch, clone_path: $path, candidates: []}'
    exit 0
}

# Collect candidate files
CANDIDATES="[]"

if [[ ${#PATH_PATTERNS[@]} -eq 0 ]]; then
    # No patterns: list all tracked files
    PATH_PATTERNS=("*")
fi

for pattern in "${PATH_PATTERNS[@]}"; do
    while IFS= read -r rel_path; do
        [[ -z "$rel_path" ]] && continue
        size=$(git_file_size "$CLONE_DIR" "$rel_path")
        CANDIDATES=$(echo "$CANDIDATES" | jq --arg fp "$rel_path" --argjson sz "$size" \
            '. + [{"file_path": $fp, "size_bytes": $sz}]')
    done < <(git_list_files "$CLONE_DIR" "$pattern")
done

# Deduplicate by file_path
CANDIDATES=$(echo "$CANDIDATES" | jq 'unique_by(.file_path)')

jq -n --arg repo "$REPO_SLUG" --arg branch "$BRANCH" --arg path "$CLONE_DIR" --argjson candidates "$CANDIDATES" \
    '{repo: $repo, branch: $branch, clone_path: $path, candidates: $candidates}'
