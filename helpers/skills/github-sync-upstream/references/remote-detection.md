# Remote Detection and Setup

## Parsing Remotes

Extract `owner/repo` from both SSH and HTTPS URLs:

```bash
git -C "${REPO_ROOT}" remote -v | grep '(fetch)' | while read -r name url _; do
  owner_repo=$(echo "${url}" | sed -E 's|.*[:/]([^/]+/[^/]+?)(\.git)?$|\1|')
  echo "${name} ${owner_repo}"
done
```

## Resolving Upstream and Target

Examine non-origin remotes:

- If a remote points to a different org but the **same repo name** as
  origin, it is a candidate (either upstream or target).
- **One** non-origin remote → ask if it is upstream or target, ask for the
  other.
- **Two or more** non-origin remotes → present them and ask which is
  upstream and which is target.
- **No** non-origin remotes → ask for both upstream (`owner/repo`) and
  target (`owner/repo`).

## Ensuring Remotes Exist

For both upstream and target, check if a remote already points to the
correct URL. If not, add or update:

```bash
# Find or create upstream remote
UPSTREAM_REMOTE=""
while read -r name url _; do
  if echo "${url}" | grep -qE "[:/]${UPSTREAM_REPO}(\.git)?$"; then
    UPSTREAM_REMOTE="${name}"
    break
  fi
done < <(git -C "${REPO_ROOT}" remote -v | grep '(fetch)')

if [ -z "${UPSTREAM_REMOTE}" ]; then
  UPSTREAM_REMOTE="upstream"
  git -C "${REPO_ROOT}" remote add "${UPSTREAM_REMOTE}" \
    "https://github.com/${UPSTREAM_REPO}.git" 2>/dev/null || \
    git -C "${REPO_ROOT}" remote set-url "${UPSTREAM_REMOTE}" \
    "https://github.com/${UPSTREAM_REPO}.git"
fi

# Find or create target remote
TARGET_REMOTE=""
while read -r name url _; do
  if echo "${url}" | grep -qE "[:/]${TARGET_REPO}(\.git)?$"; then
    TARGET_REMOTE="${name}"
    break
  fi
done < <(git -C "${REPO_ROOT}" remote -v | grep '(fetch)')

if [ -z "${TARGET_REMOTE}" ]; then
  TARGET_REMOTE="target"
  git -C "${REPO_ROOT}" remote add "${TARGET_REMOTE}" \
    "https://github.com/${TARGET_REPO}.git" 2>/dev/null || \
    git -C "${REPO_ROOT}" remote set-url "${TARGET_REMOTE}" \
    "https://github.com/${TARGET_REPO}.git"
fi
```

## Clone From Scratch (Path B)

When the user is not inside the target repo but has a GitHub fork:

```bash
# Clone the user's fork into a temp dir
# FORK_REPO is the user's fork (e.g., "myuser/workload-variant-autoscaler")
REPO_ROOT=$(mktemp -d)
git clone "https://github.com/${FORK_REPO}.git" "${REPO_ROOT}"
```

After cloning, `origin` points to the user's fork. Add remotes for the
upstream source and the target (PR destination):

```bash
git -C "${REPO_ROOT}" remote add target \
  "https://github.com/${TARGET_REPO}.git"
git -C "${REPO_ROOT}" remote add upstream \
  "https://github.com/${UPSTREAM_REPO}.git"
```

Verify with `git -C "${REPO_ROOT}" remote -v`. The user pushes the sync
branch to `origin` (their fork) and opens a PR against `TARGET_REPO`.

If the user does **not** have a fork, ask them to create one first
(e.g., via the GitHub UI or any method they prefer), then re-run the
skill.
