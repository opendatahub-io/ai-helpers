#!/bin/bash
# Ensure upstream and target GitHub remotes exist and fetch their branches.
#
# Checks if remotes already point to the given repos. If not, adds or
# updates them. Then fetches the specified branches.
#
# Usage:
#   bash setup-remotes.sh \
#     --repo /path/to/repo \
#     --upstream-repo upstream-org/my-project \
#     --target-repo target-org/my-project \
#     --upstream-branch main \
#     --target-branch main
#
# Output (tab-separated):
#   UPSTREAM_REMOTE	upstream
#   TARGET_REMOTE	opendatahub

set -euo pipefail

REPO=""
UPSTREAM_REPO=""
TARGET_REPO=""
UPSTREAM_BRANCH="main"
TARGET_BRANCH="main"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)             REPO="$2"; shift 2;;
    --upstream-repo)    UPSTREAM_REPO="$2"; shift 2;;
    --target-repo)      TARGET_REPO="$2"; shift 2;;
    --upstream-branch)  UPSTREAM_BRANCH="$2"; shift 2;;
    --target-branch)    TARGET_BRANCH="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "${REPO}" || -z "${UPSTREAM_REPO}" || -z "${TARGET_REPO}" ]]; then
  echo "Error: --repo, --upstream-repo, and --target-repo are required" >&2
  exit 1
fi

find_or_create_remote() {
  local repo_path="$1"
  local target_owner_repo="$2"
  local default_name="$3"

  local found_name=""
  while read -r name url _; do
    if echo "${url}" | grep -qE "[:/]${target_owner_repo}(\.git)?$"; then
      found_name="${name}"
      break
    fi
  done < <(git -C "${repo_path}" remote -v | grep '(fetch)')

  if [[ ! "${target_owner_repo}" =~ ^[^/]+/[^/]+$ ]]; then
    echo "Error: invalid owner/repo format: ${target_owner_repo}" >&2
    return 1
  fi

  if [[ -z "${found_name}" ]]; then
    found_name="${default_name}"
    if git -C "${repo_path}" remote get-url "${found_name}" >/dev/null 2>&1; then
      git -C "${repo_path}" remote set-url "${found_name}" \
        "https://github.com/${target_owner_repo}.git"
    else
      git -C "${repo_path}" remote add "${found_name}" \
        "https://github.com/${target_owner_repo}.git"
    fi
  fi

  echo "${found_name}"
}

UPSTREAM_REMOTE=$(find_or_create_remote "${REPO}" "${UPSTREAM_REPO}" "upstream")
TARGET_REMOTE=$(find_or_create_remote "${REPO}" "${TARGET_REPO}" "target")

git -C "${REPO}" fetch "${UPSTREAM_REMOTE}" "${UPSTREAM_BRANCH}" 2>&1
git -C "${REPO}" fetch "${TARGET_REMOTE}" "${TARGET_BRANCH}" 2>&1

printf 'UPSTREAM_REMOTE\t%s\n' "${UPSTREAM_REMOTE}"
printf 'TARGET_REMOTE\t%s\n' "${TARGET_REMOTE}"
