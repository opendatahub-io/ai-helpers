#!/usr/bin/env bash
# Git utility functions for branch resolution and file listing.
#
# Source this file to get helper functions:
#   source "${CLAUDE_SKILL_DIR}/scripts/git-utils.sh"
#
# Requires: git, jq

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"

# Load .env if available (GITHUB_TOKEN, etc.)
source "${SCRIPTS_DIR}/load-env.sh"

WORKSPACE="${PROJECT_ROOT}/workspace/repos"

# git_clone_or_fetch <repo-slug> <branch>
# Clone a repo if not present, or fetch the specified branch.
# Returns the path to the cloned repo.
git_clone_or_fetch() {
    local repo_slug="$1"
    local branch="$2"
    local clone_dir="${WORKSPACE}/${repo_slug}"

    if [[ -d "${clone_dir}/.git" ]]; then
        git -C "${clone_dir}" fetch origin "${branch}" --depth=1 2>/dev/null || true
        git -C "${clone_dir}" checkout "origin/${branch}" --force 2>/dev/null || \
            git -C "${clone_dir}" checkout "${branch}" --force 2>/dev/null || true
    else
        mkdir -p "$(dirname "${clone_dir}")"
        git clone --depth=1 --branch "${branch}" "https://github.com/${repo_slug}.git" "${clone_dir}" 2>/dev/null
    fi
    echo "${clone_dir}"
}

# git_list_files <repo-path> [glob-pattern]
# List files in a repo matching an optional glob pattern.
# Returns one file path per line, relative to the repo root.
git_list_files() {
    local repo_path="$1"
    local pattern="${2:-}"

    if [[ -n "$pattern" ]]; then
        git -C "$repo_path" ls-files "$pattern" 2>/dev/null || true
    else
        git -C "$repo_path" ls-files 2>/dev/null || true
    fi
}

# git_list_remote_branches <repo-path>
# List remote branch names for a repo.
git_list_remote_branches() {
    local repo_path="$1"
    git -C "$repo_path" branch -r --format='%(refname:short)' 2>/dev/null | \
        sed 's|^origin/||' || true
}

# git_resolve_branch <repo-path> <version> <branch-template>
# Resolve a product version to a branch name.
# Tries exact match first, then pattern-based resolution.
# Returns the branch name or the template as fallback.
git_resolve_branch() {
    local repo_path="$1"
    local version="$2"
    local branch_template="$3"

    # Try direct substitution
    local candidate_branch="${branch_template/\{version\}/$version}"

    # Check if this branch exists
    if git -C "$repo_path" rev-parse --verify "origin/${candidate_branch}" >/dev/null 2>&1; then
        echo "$candidate_branch"
        return 0
    fi

    # Try without the template (use version directly as branch)
    if git -C "$repo_path" rev-parse --verify "origin/release-${version}" >/dev/null 2>&1; then
        echo "release-${version}"
        return 0
    fi

    # Fallback to template default (strip {version} placeholder)
    local fallback="${branch_template/\{version\}/}"
    fallback="${fallback:-main}"
    echo "$fallback"
}

# git_file_content <repo-path> <file-path>
# Read a file from the repo working tree.
git_file_content() {
    local repo_path="$1"
    local file_path="$2"
    cat "${repo_path}/${file_path}" 2>/dev/null
}

# git_file_size <repo-path> <file-path>
# Return the size in bytes of a file in the repo.
git_file_size() {
    local repo_path="$1"
    local file_path="$2"
    stat -c%s "${repo_path}/${file_path}" 2>/dev/null || \
        stat -f%z "${repo_path}/${file_path}" 2>/dev/null || echo 0
}
