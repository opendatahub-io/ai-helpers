# Conflict Resolution

## Resolving Merge Conflicts

If the merge step produces conflicts:

1. List conflicted files:
   ```bash
   git -C "${REPO_ROOT}" diff --name-only --diff-filter=U
   ```

2. **Auto-resolve protected files** — for any conflicted file matching a
   pattern in `PROTECTED_PATTERNS`, resolve by keeping the target version:
   ```bash
   git -C "${REPO_ROOT}" checkout "${TARGET_REMOTE}/${TARGET_BRANCH}" \
     -- "${file}"
   git -C "${REPO_ROOT}" add "${file}"
   ```

3. Show remaining conflicts to the user.

4. Attempt to resolve trivial conflicts automatically (whitespace, import
   order).

5. For non-trivial conflicts, show the diff and ask the user how to
   resolve each file.

6. After all conflicts are resolved:
   ```bash
   git -C "${REPO_ROOT}" add -u
   git -C "${REPO_ROOT}" commit --no-edit
   ```

## Restoring Protected Files

After merge (whether clean or after conflict resolution), restore
protected files to the target version. Skip if `PROTECTED_PATTERNS` is
empty.

```bash
RESTORED=false
for file in $(git -C "${REPO_ROOT}" diff --name-only \
  "${TARGET_REMOTE}/${TARGET_BRANCH}" HEAD 2>/dev/null); do
  for pattern in ${PROTECTED_PATTERNS}; do
    case "${file}" in
      ${pattern})
        echo "Restoring protected file: ${file}"
        git -C "${REPO_ROOT}" checkout \
          "${TARGET_REMOTE}/${TARGET_BRANCH}" -- "${file}"
        RESTORED=true
        ;;
    esac
  done
done
if [ "${RESTORED}" = true ]; then
  git -C "${REPO_ROOT}" add -u
  git -C "${REPO_ROOT}" commit --amend --no-edit
fi
```

## Scanning for Leftover Conflict Markers

Git can report a clean merge while leaving conflict markers in files:

```bash
CONFLICT_FILES=$(git -C "${REPO_ROOT}" grep -rlE '^(<{4,}|={4,}|>{4,})' \
  || true)
if [ -n "${CONFLICT_FILES}" ]; then
  echo "Conflict markers found after merge:"
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    echo "--- ${f} ---"
    git -C "${REPO_ROOT}" grep -nE '^(<{4,}|={4,}|>{4,})' "${f}"
  done <<< "${CONFLICT_FILES}"
fi
```

If markers are found, treat them as unresolved conflicts — show them to
the user and ask how to resolve.

## Error Handling

- If the user-provided SHA does not exist on the upstream branch, report
  the error and ask for a valid SHA.
- If conflicts cannot be resolved, abort and clean up:
  ```bash
  git -C "${REPO_ROOT}" merge --abort
  git -C "${REPO_ROOT}" checkout "${ORIGINAL_BRANCH}"
  git -C "${REPO_ROOT}" branch -D "${BRANCH}"
  ```
- If a branch already exists, ask whether to force-update or skip.
- On any failure after branch creation, clean up:
  ```bash
  git -C "${REPO_ROOT}" checkout "${ORIGINAL_BRANCH}"
  git -C "${REPO_ROOT}" branch -D "${BRANCH}"
  ```
- Always return the PR URL on success.
