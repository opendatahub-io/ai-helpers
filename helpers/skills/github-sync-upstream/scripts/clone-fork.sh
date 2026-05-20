#!/bin/bash
# Clone a user's GitHub fork into a temporary directory and set up remotes.
#
# Usage:
#   bash clone-fork.sh \
#     --fork-repo user/my-project \
#     --upstream-repo upstream-org/my-project \
#     --target-repo target-org/my-project
#
# Output:
#   REPO_ROOT	/tmp/tmp.XXXXXX

set -euo pipefail

FORK_REPO=""
UPSTREAM_REPO=""
TARGET_REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fork-repo)     FORK_REPO="$2"; shift 2;;
    --upstream-repo) UPSTREAM_REPO="$2"; shift 2;;
    --target-repo)   TARGET_REPO="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "${FORK_REPO}" || -z "${UPSTREAM_REPO}" || -z "${TARGET_REPO}" ]]; then
  echo "Error: --fork-repo, --upstream-repo, and --target-repo are required" >&2
  exit 1
fi

for _var_name in FORK_REPO UPSTREAM_REPO TARGET_REPO; do
  _val="${!_var_name}"
  if [[ ! "${_val}" =~ ^[^/]+/[^/]+$ ]]; then
    echo "Error: --$(echo "${_var_name}" | tr '[:upper:]_' '[:lower:]-') must be in owner/repo format, got: ${_val}" >&2
    exit 1
  fi
done

PARENT_DIR=$(mktemp -d)
REPO_NAME=$(echo "${FORK_REPO}" | cut -d/ -f2)
REPO_ROOT="${PARENT_DIR}/${REPO_NAME}"
git clone "https://github.com/${FORK_REPO}.git" "${REPO_ROOT}" 2>&1

if git -C "${REPO_ROOT}" remote get-url upstream >/dev/null 2>&1; then
  git -C "${REPO_ROOT}" remote set-url upstream \
    "https://github.com/${UPSTREAM_REPO}.git"
else
  git -C "${REPO_ROOT}" remote add upstream \
    "https://github.com/${UPSTREAM_REPO}.git"
fi

if git -C "${REPO_ROOT}" remote get-url target >/dev/null 2>&1; then
  git -C "${REPO_ROOT}" remote set-url target \
    "https://github.com/${TARGET_REPO}.git"
else
  git -C "${REPO_ROOT}" remote add target \
    "https://github.com/${TARGET_REPO}.git"
fi

printf 'REPO_ROOT\t%s\n' "${REPO_ROOT}"
