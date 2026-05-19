#!/bin/bash
# Detect and classify GitHub remotes for a repository.
#
# Parses git remote -v output and extracts owner/repo for each remote.
# Handles both SSH (git@github.com:owner/repo.git) and HTTPS URLs.
#
# Usage:
#   bash detect-remotes.sh --repo /path/to/repo
#
# Output (one line per remote, tab-separated):
#   origin	zdtsw-forking/workload-variant-autoscaler
#   upstream	llm-d/llm-d-workload-variant-autoscaler

set -euo pipefail

REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "Error: --repo requires a value" >&2; exit 1; }
      REPO="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "${REPO}" ]]; then
  echo "Error: --repo is required" >&2
  exit 1
fi

if ! git -C "${REPO}" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Error: ${REPO} is not a git repository" >&2
  exit 1
fi

git -C "${REPO}" remote -v | awk '$3=="(fetch)"' | while read -r name url _; do
  owner_repo=$(echo "${url}" | sed -E 's|.*[:/]([^/]+/[^/]+?)(\.git)?$|\1|')
  if [[ ! "${owner_repo}" =~ ^[^/]+/[^/]+$ ]]; then
    echo "Warning: malformed URL for remote ${name}: ${url}" >&2
    continue
  fi
  printf '%s\t%s\n' "${name}" "${owner_repo}"
done
