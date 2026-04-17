#!/usr/bin/env bash
# Shell helpers for accessing product configuration.
#
# Source this file to get helper functions:
#   source "${CLAUDE_SKILL_DIR}/scripts/product-config.sh"
#
# Requires: python3, jq
# Assumes: working directory is the project root

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"

# Load .env if available (PRODUCT_CONFIG override, etc.)
source "${SCRIPTS_DIR}/load-env.sh"

CONFIG_PATH="${PRODUCT_CONFIG:-${PROJECT_ROOT}/configs/rhoai.yaml}"
PARSE_SCRIPT="${SCRIPTS_DIR}/parse-product-config.py"

# pc_section <section-name>
# Extract a section from product config as JSON.
pc_section() {
    python3 "$PARSE_SCRIPT" "$CONFIG_PATH" --section "$1"
}

# pc_resolve_component <jira-component-name>
# Resolve a Jira component name to its canonical key and repo.
# Returns JSON: {"found": true, "key": "...", "repo": "...", "jira_names": [...]}
pc_resolve_component() {
    python3 "$PARSE_SCRIPT" "$CONFIG_PATH" --resolve-component "$1"
}

# pc_resolve_version <jira-version-string>
# Resolve a Jira version string to a branch name.
# Returns JSON: {"matched": true, "version": "...", "branch": "..."}
pc_resolve_version() {
    python3 "$PARSE_SCRIPT" "$CONFIG_PATH" --resolve-version "$1"
}

# pc_product_id
# Return the product_id from config.
pc_product_id() {
    python3 "$PARSE_SCRIPT" "$CONFIG_PATH" | jq -r '.product_id'
}

# pc_docs_repo
# Return the documentation repository slug.
pc_docs_repo() {
    pc_section docs | jq -r '.repo'
}

# pc_docs_branch
# Return the documentation branch template.
pc_docs_branch() {
    pc_section docs | jq -r '.branch_template'
}

# pc_module_prefix <type>
# Return the module prefix for a given type (concept, procedure, reference, assembly, snippet).
pc_module_prefix() {
    pc_section docs | jq -r ".module_prefixes.\"$1\" // empty"
}

# pc_context_repos
# Return a newline-separated list of repos from context sources.
pc_context_repos() {
    pc_section context_sources | jq -r '.[].repo'
}

# pc_always_include_repos
# Return repos that have always_include=true.
pc_always_include_repos() {
    pc_section context_sources | jq -r '.[] | select(.always_include == true) | .repo'
}

# pc_component_repo <component-key>
# Return the repo for a given component key.
pc_component_repo() {
    pc_section component_repo_map | jq -r ".\"$1\" // empty"
}

# pc_jira_project_keys
# Return Jira project keys as a newline-separated list.
pc_jira_project_keys() {
    pc_section jira | jq -r '.project_keys[]'
}
