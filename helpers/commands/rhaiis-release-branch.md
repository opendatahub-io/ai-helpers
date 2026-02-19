---
description: Create release branches and enable repeatable builds for a RHAIIS release
argument-hint: <epic-key> <version>
---

## Name
odh-ai-helpers:rhaiis-release-branch

## Synopsis
```
/rhaiis:release-branch INFERENG-4584 3.3  # Create release branches for version 3.3
```

## Description
Automates two steps of RHAIIS release preparation:
- **Step 2**: Create release branches in `rhaiis/pipeline` and `rhaiis/containers` from the correct commits
- **Step 3**: Enable repeatable builds on the new pipeline release branch

This command traces from the released production image back to the exact commits in both repos, creates release branches at those commits, and submits an MR to enable repeatable builds.

**GitLab repositories:**

| Repository | Encoded Path |
|------------|-------------|
| `rhaiis/pipeline` | `redhat%2Frhel-ai%2Frhaiis%2Fpipeline` |
| `rhaiis/containers` | `redhat%2Frhel-ai%2Frhaiis%2Fcontainers` |

**JIRA transitions:** In Progress = `41`, Closed = `61`

## Implementation

### Step 0: Gather Parameters

Ask the user for:
1. **EPIC_KEY** - The release prep epic key (e.g. `INFERENG-4584`)
2. **RELEASE_VERSION** - The version being branched off (e.g. `3.3`)

### Step 1: Find JIRA Stories

Search for child stories under the epic (`"Epic Link" = <EPIC_KEY>`) and match by summary pattern:

- **Step 2 story**: Summary contains "Step 2:" (create branches)
- **Step 3 story**: Summary contains "Step 3:" (enable repeatable builds)

Transition both to "In Progress" (id: 41).

### Phase 1: Find the Correct Commits to Branch From

The command traces from the released production image back to the exact commits in both repos, producing TWO commit SHAs: one for `containers` and one for `pipeline`.

**Step 1a** - Find the latest released RHAIIS image version:

Ask the user for the full version string (e.g. `3.3.0-1768563084`), or help them find it:
```bash
curl -s "https://catalog.redhat.com/api/containers/v1/repositories/registry/registry.access.redhat.com/repository/rhaiis/vllm-cuda-rhel9/images?page_size=20&sort_by=last_update_date%5Bdesc%5D" | \
  jq -r '.data[] | "\(.architecture): \(.repositories[0].manifest_list_digest // .repositories[0].manifest_schema2_digest) - tags: \(.repositories[0].tags | map(.name) | join(", "))"'
```

**Step 1b** - Find the matching Quay.io image and extract git commit labels:
```bash
skopeo inspect --no-tags --override-arch amd64 --override-os linux \
  docker://quay.io/aipcc/rhaiis/cuda-ubi9:<FULL_VERSION> | \
  jq '{git_url: .Labels["git.url"], git_commit: .Labels["git.commit"], release: .Labels["release"], version: .Labels["version"]}'
```
This yields `CONTAINERS_COMMIT` from `git.commit`.

**Step 1c** - Verify the containers commit and extract wheel version:
```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/repository/commits/<CONTAINERS_COMMIT>" | \
  jq '{id: .id[:12], title: .title, created_at: .created_at}'

glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/repository/files/build-args%2Fcuda-ubi9.conf?ref=<CONTAINERS_COMMIT>" | \
  jq -r '.content' | base64 -d | grep -E "^WHEEL_RELEASE"
```

**Step 1d** - Find the matching pipeline commit by wheel tag:
```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Frhaiis%2Fpipeline/repository/tags?per_page=20" | \
  jq -r '.[] | "\(.name) -> \(.commit.id[:12])"' | grep "<WHEEL_VERSION>"
```
The commit SHA from the matching tag becomes `PIPELINE_COMMIT`.

**Step 1e** - Present both commits for confirmation:

| Repo | Commit | Source |
|------|--------|--------|
| `rhaiis/containers` | `<CONTAINERS_COMMIT>` | From quay.io image labels |
| `rhaiis/pipeline` | `<PIPELINE_COMMIT>` | From wheel release tag |

Ask user to confirm before proceeding.

### Phase 2: Create and Protect Branches

Branch name: `<RELEASE_VERSION>` (e.g. `3.3`)

1. **Create branch in pipeline repo:**
   ```bash
   glab api --hostname gitlab.com --method POST \
     "projects/redhat%2Frhel-ai%2Frhaiis%2Fpipeline/repository/branches" \
     -f branch="<RELEASE_VERSION>" -f ref="<PIPELINE_COMMIT>"
   ```

2. **Create branch in containers repo:**
   ```bash
   glab api --hostname gitlab.com --method POST \
     "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/repository/branches" \
     -f branch="<RELEASE_VERSION>" -f ref="<CONTAINERS_COMMIT>"
   ```

3. **Verify creation:**
   ```bash
   glab api --hostname gitlab.com \
     "projects/redhat%2Frhel-ai%2Frhaiis%2Fpipeline/repository/branches/<RELEASE_VERSION>" | \
     jq '{name: .name, commit: .commit.id[:12]}'

   glab api --hostname gitlab.com \
     "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/repository/branches/<RELEASE_VERSION>" | \
     jq '{name: .name, commit: .commit.id[:12]}'
   ```

4. **Protect branches** (attempt via API, fallback to Settings UI URLs):
   ```bash
   glab api --hostname gitlab.com --method POST \
     "projects/redhat%2Frhel-ai%2Frhaiis%2Fpipeline/protected_branches" \
     -f name="<RELEASE_VERSION>"

   glab api --hostname gitlab.com --method POST \
     "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/protected_branches" \
     -f name="<RELEASE_VERSION>"
   ```

   If protection fails due to permissions, provide the Settings UI URLs:
   - Pipeline: `https://gitlab.com/redhat/rhel-ai/rhaiis/pipeline/-/settings/repository#js-protected-branches-settings`
   - Containers: `https://gitlab.com/redhat/rhel-ai/rhaiis/containers/-/settings/repository#js-protected-branches-settings`

5. Add comment to Step 2 JIRA story with branch creation details and links.
6. Transition Step 2 story to "Closed" (id: 61).

### Phase 3: Enable Repeatable Builds (MR to Release Branch)

Reference MR: `rhaiis/pipeline MR !76`

1. Locate or clone the pipeline repo (check workspace first, then clone if needed)
2. Fetch and checkout the release branch
3. Create feature branch named `<STEP3_JIRA_TICKET>-enable-repeatable-builds`
4. Uncomment all `ENABLE_REPEATABLE_BUILD_MODE` lines in `.gitlab-ci.yml`:
   - Replace `      # ENABLE_REPEATABLE_BUILD_MODE: true` with `      ENABLE_REPEATABLE_BUILD_MODE: true` (replace_all)
5. Verify: `grep -c 'ENABLE_REPEATABLE_BUILD_MODE: true'` should equal 15 and no commented instances remain
6. Stage `.gitlab-ci.yml`
7. Commit with AIPCC format, push, and create MR targeting the release branch (use the `aipcc-commit` skill with `--push`)
8. Add comment to Step 3 JIRA story with the MR link
9. Inform the user: Midstream team needs to approve and merge

### Cleanup

Summarize what was done: branches created, MR created, JIRA stories updated.

## Examples

### Create release branches
```bash
/rhaiis:release-branch INFERENG-4584 3.3
```

## Arguments

- **epic-key** (required): JIRA epic key for the release prep epic
  - Example: `INFERENG-4584`

- **version** (required): Release version to branch
  - Example: `3.3`

## See Also
- **`/rhaiis:release-infra`** - Add infrastructure version entry
- **`/rhaiis:release-packages`** - Identify package changes between versions
- **`/rhaiis:release-renovate`** - Update Renovate configs for release
