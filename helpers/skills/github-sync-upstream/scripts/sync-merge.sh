#!/bin/bash
# Create a sync branch, merge upstream GitHub commits, restore protected
# files, and scan for leftover conflict markers.
#
# Usage:
#   bash sync-merge.sh \
#     --repo /path/to/repo \
#     --upstream-remote upstream \
#     --upstream-branch main \
#     --target-remote opendatahub \
#     --target-branch main \
#     --upstream-repo upstream-org/my-project \
#     [--commit <sha>] \
#     [--protected-patterns "/OWNERS /OWNERS_ALIASES .tekton/*.yaml Dockerfile*konflux"] \
#     [--co-author "Claude <noreply@anthropic.com>"]
#
# --co-author is optional: when set, a "Co-authored-by:" trailer is appended
# to the merge commit so the agent driving the sync is credited alongside the
# human author. Carries onto the conflict-resolve and protected-file commits.
#
# Exit codes:
#   0 = clean merge (or clean after protected file restore)
#   1 = unresolved conflicts remain (details printed to stdout)
#   2 = argument/setup error
#   3 = duplicate branch exists (DUPLICATE_BRANCH lines printed to stdout)
#   4 = nothing to sync (target already up to date; no branch created)
#
# Output on success:
#   BRANCH	sync/upstream-<short_sha>
#   FULL_SHA	<full_sha>
#   SHORT_SHA	<short_sha>
#   COMMIT_COUNT	<N>

set -euo pipefail

REPO=""
UPSTREAM_REMOTE=""
UPSTREAM_BRANCH="main"
TARGET_REMOTE=""
TARGET_BRANCH="main"
UPSTREAM_REPO=""
COMMIT=""
PROTECTED_PATTERNS=""
CO_AUTHOR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)                REPO="$2"; shift 2;;
    --upstream-remote)     UPSTREAM_REMOTE="$2"; shift 2;;
    --upstream-branch)     UPSTREAM_BRANCH="$2"; shift 2;;
    --target-remote)       TARGET_REMOTE="$2"; shift 2;;
    --target-branch)       TARGET_BRANCH="$2"; shift 2;;
    --upstream-repo)       UPSTREAM_REPO="$2"; shift 2;;
    --commit)              COMMIT="$2"; shift 2;;
    --protected-patterns)  PROTECTED_PATTERNS="$2"; shift 2;;
    --co-author)           CO_AUTHOR="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

if [[ -z "${REPO}" || -z "${UPSTREAM_REMOTE}" || -z "${TARGET_REMOTE}" || -z "${UPSTREAM_REPO}" ]]; then
  echo "Error: --repo, --upstream-remote, --target-remote, and --upstream-repo are required" >&2
  exit 2
fi

# Match a file path against a protected pattern. A leading '/' anchors the
# pattern to the repo root (e.g. '/OWNERS' matches only the top-level OWNERS,
# not nested ones). A pattern that otherwise contains '/' matches the relative
# path. A bare pattern matches the basename anywhere in the tree.
matches_protected() {
  local file="$1"
  local basename
  basename=$(basename "${file}")
  # Split on whitespace without glob-expanding the patterns against the cwd.
  local -a patterns
  read -ra patterns <<<"${PROTECTED_PATTERNS}"
  local pattern
  for pattern in "${patterns[@]}"; do
    if [[ "${pattern}" == /* ]]; then
      # shellcheck disable=SC2254
      case "${file}" in
        ${pattern#/}) return 0;;
      esac
    elif [[ "${pattern}" == */* ]]; then
      # shellcheck disable=SC2254
      case "${file}" in
        ${pattern}) return 0;;
      esac
    else
      # shellcheck disable=SC2254
      case "${basename}" in
        ${pattern}) return 0;;
      esac
    fi
  done
  return 1
}

# Resolve target commit
TARGET_COMMIT="${COMMIT:-${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}}"
FULL_SHA=$(git -C "${REPO}" rev-parse "${TARGET_COMMIT}")
SHORT_SHA=$(git -C "${REPO}" rev-parse --short "${TARGET_COMMIT}")

if ! git -C "${REPO}" merge-base --is-ancestor "${FULL_SHA}" \
  "${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"; then
  echo "Error: commit ${FULL_SHA} is not on ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}" >&2
  exit 2
fi

COMMIT_COUNT=$(git -C "${REPO}" log \
  "${TARGET_REMOTE}/${TARGET_BRANCH}..${FULL_SHA}" --oneline | wc -l)

# Nothing to sync: the target already contains the upstream tip. Exit early —
# before creating a branch, merging, or pushing — so we never leave empty
# branches behind or open empty PRs, and we don't waste any further work.
if [[ "${COMMIT_COUNT}" -eq 0 ]]; then
  echo "NOTHING_TO_SYNC	${TARGET_REMOTE}/${TARGET_BRANCH} already up to date with ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH} (${SHORT_SHA})"
  printf 'FULL_SHA\t%s\n'    "${FULL_SHA}"
  printf 'SHORT_SHA\t%s\n'   "${SHORT_SHA}"
  printf 'COMMIT_COUNT\t0\n'
  exit 4
fi

# Show summary
echo "=== Sync Summary ==="
echo "Target: ${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH} (${SHORT_SHA})"
echo "Into:   ${TARGET_REMOTE}/${TARGET_BRANCH}"
echo ""
echo "=== Commits to be synced (${COMMIT_COUNT}) ==="
git -C "${REPO}" log \
  "${TARGET_REMOTE}/${TARGET_BRANCH}..${FULL_SHA}" --oneline
echo ""
echo "=== File changes ==="
git -C "${REPO}" diff --stat \
  "${TARGET_REMOTE}/${TARGET_BRANCH}...${FULL_SHA}"
echo ""

# Check for duplicate branches
BRANCH="sync/upstream-${SHORT_SHA}"
HAS_DUPLICATE=false

if git -C "${REPO}" show-ref --verify --quiet "refs/heads/${BRANCH}" 2>/dev/null; then
  echo "DUPLICATE_BRANCH	local	${BRANCH}"
  HAS_DUPLICATE=true
fi
if git -C "${REPO}" show-ref --verify --quiet "refs/remotes/origin/${BRANCH}" 2>/dev/null; then
  echo "DUPLICATE_BRANCH	remote	origin/${BRANCH}"
  HAS_DUPLICATE=true
fi

if [[ "${HAS_DUPLICATE}" == "true" ]]; then
  printf 'BRANCH\t%s\n' "${BRANCH}"
  printf 'FULL_SHA\t%s\n' "${FULL_SHA}"
  printf 'SHORT_SHA\t%s\n' "${SHORT_SHA}"
  printf 'COMMIT_COUNT\t%s\n' "${COMMIT_COUNT}"
  exit 3
fi

# Create sync branch
git -C "${REPO}" checkout -b "${BRANCH}" "${TARGET_REMOTE}/${TARGET_BRANCH}"

# Merge
MERGE_FAILED=false
# Build the merge message, appending a Co-authored-by trailer when requested
# (e.g. to credit the agent that drove the sync alongside the human author).
# The message is stored in MERGE_MSG so it is reused on the conflict-resolve
# `git commit --no-edit` and the protected-file `--amend` paths below.
MERGE_MSG="Sync upstream ${UPSTREAM_REPO} ${SHORT_SHA}"
if [[ -n "${CO_AUTHOR}" ]]; then
  MERGE_MSG="${MERGE_MSG}"$'\n\n'"Co-authored-by: ${CO_AUTHOR}"
fi
git -C "${REPO}" merge --no-ff "${FULL_SHA}" --no-edit \
  -m "${MERGE_MSG}" || MERGE_FAILED=true

if [[ "${MERGE_FAILED}" == "true" ]]; then
  # Auto-resolve protected files if patterns are set
  if [[ -n "${PROTECTED_PATTERNS}" ]]; then
    while IFS= read -r file; do
      [[ -z "${file}" ]] && continue
      if matches_protected "${file}"; then
        if git -C "${REPO}" cat-file -e "${TARGET_REMOTE}/${TARGET_BRANCH}:${file}" 2>/dev/null; then
          echo "Auto-resolving protected file: ${file}"
          git -C "${REPO}" checkout "${TARGET_REMOTE}/${TARGET_BRANCH}" -- "${file}"
          git -C "${REPO}" add "${file}"
        else
          echo "Auto-resolving protected file (remove, absent from target): ${file}"
          git -C "${REPO}" rm -q -- "${file}"
        fi
      fi
    done < <(git -C "${REPO}" diff --name-only --diff-filter=U 2>/dev/null || true)
  fi

  # Check if conflicts remain
  REMAINING=$(git -C "${REPO}" diff --name-only --diff-filter=U 2>/dev/null || true)
  if [[ -n "${REMAINING}" ]]; then
    echo ""
    echo "UNRESOLVED_CONFLICTS"
    echo "${REMAINING}"
    exit 1
  fi

  git -C "${REPO}" add -u
  git -C "${REPO}" commit --no-edit
fi

# Restore protected files (even after clean merge)
if [[ -n "${PROTECTED_PATTERNS}" ]]; then
  RESTORED=false
  while IFS= read -r file; do
    [[ -z "${file}" ]] && continue
    if matches_protected "${file}"; then
      if git -C "${REPO}" cat-file -e "${TARGET_REMOTE}/${TARGET_BRANCH}:${file}" 2>/dev/null; then
        echo "Restoring protected file: ${file}"
        git -C "${REPO}" checkout "${TARGET_REMOTE}/${TARGET_BRANCH}" -- "${file}"
      else
        echo "Removing protected file absent from target: ${file}"
        git -C "${REPO}" rm -q -- "${file}"
      fi
      RESTORED=true
    fi
  done < <(git -C "${REPO}" diff --name-only \
    "${TARGET_REMOTE}/${TARGET_BRANCH}" HEAD 2>/dev/null)
  if [[ "${RESTORED}" == "true" ]]; then
    git -C "${REPO}" add -u
    git -C "${REPO}" commit --amend --no-edit
  fi
fi

# Scan for leftover conflict markers
CONFLICT_MARKERS=$(git -C "${REPO}" grep -rlE '^(<{4,}|={4,}|>{4,})' || true)
if [[ -n "${CONFLICT_MARKERS}" ]]; then
  echo ""
  echo "CONFLICT_MARKERS_FOUND"
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    echo "--- ${f} ---"
    git -C "${REPO}" grep -nE '^(<{4,}|={4,}|>{4,})' "${f}"
  done <<< "${CONFLICT_MARKERS}"
  exit 1
fi

# Success output
printf 'BRANCH\t%s\n' "${BRANCH}"
printf 'FULL_SHA\t%s\n' "${FULL_SHA}"
printf 'SHORT_SHA\t%s\n' "${SHORT_SHA}"
printf 'COMMIT_COUNT\t%s\n' "${COMMIT_COUNT}"
