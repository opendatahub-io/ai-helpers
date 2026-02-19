---
description: Update Renovate configs and product version for a RHAIIS release
argument-hint: <epic-key> <release-branch> <next-version>
---

## Name
odh-ai-helpers:rhaiis-release-renovate

## Synopsis
```
/rhaiis:release-renovate INFERENG-4584 3.3 3.4EA1  # Update Renovate for 3.3 release
```

## Description
Automates three steps of RHAIIS release preparation:
- **Step 5**: Update Renovate config in pipeline repo to pin builder image for the release branch
- **Step 6**: Update PRODUCT_VERSION in pipeline repo for the next release
- **Step 7**: Update Renovate config in containers repo for base image version rules

Reference MR for Steps 5+6: `rhaiis/pipeline MR !301` (3.2.5 to 3.3 transition).

**GitLab repositories:**

| Repository | Encoded Path |
|------------|-------------|
| `rhaiis/pipeline` | `redhat%2Frhel-ai%2Frhaiis%2Fpipeline` |
| `rhaiis/containers` | `redhat%2Frhel-ai%2Frhaiis%2Fcontainers` |
| `wheels/builder` | `redhat%2Frhel-ai%2Fwheels%2Fbuilder` |

**JIRA transitions:** In Progress = `41`, Closed = `61`

## Implementation

### Step 0: Gather Parameters

Ask the user for:
1. **EPIC_KEY** - The release prep epic key (e.g. `INFERENG-4584`)
2. **RELEASE_BRANCH** - The just-created release branch (e.g. `3.3`)
3. **NEXT_VERSION** - The upcoming PRODUCT_VERSION (e.g. `3.4EA1`)

### Step 1: Find JIRA Stories

Search for child stories under the epic (`"Epic Link" = <EPIC_KEY>`).

Find:
- **Step 5 story**: Summary contains "Step 5:" (pipeline renovate)
- **Step 6 story**: Summary contains "Step 6:" (product version) — may be a duplicate of Step 5
- **Step 7 story**: Summary contains "Step 7:" (containers renovate)

Transition all found stories to "In Progress" (id: 41).

### Part A: Pipeline Repo (Steps 5+6 — One MR)

#### A1: Fetch builder version from release branch

```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Frhaiis%2Fpipeline/repository/files/builder-image-version.yml?ref=<RELEASE_BRANCH>" | \
  jq -r '.content' | base64 -d
```

Extract the builder version series. For example, if the builder version is `v25.8.3`, the regex pattern is `v25\\.8\\.` and the `allowedVersions` regex is `/^v25\\.8\\.\\d+$/`.

#### A2: Fetch current renovate.json from main

```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Frhaiis%2Fpipeline/repository/files/renovate.json?ref=main" | \
  jq -r '.content' | base64 -d
```

#### A3: Generate new renovate block

Add the following block after the last `builder-image` groupName block in `renovate.json`:

```json
{
  "matchPackageNames": [
    "redhat/rhel-ai/wheels/builder"
  ],
  "enabled": true,
  "groupName": "builder-image",
  "allowedVersions": "/^v<MAJOR>\\.<MINOR>\\.\\d+$/",
  "matchBaseBranches": [
    "<RELEASE_BRANCH>"
  ]
}
```

Where `<MAJOR>.<MINOR>` comes from the builder version extracted in A1.

#### A4: Fetch latest builder tag

```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Fwheels%2Fbuilder/repository/tags?order_by=version&sort=desc&per_page=1" | \
  jq -r '.[0].name'
```

This returns the latest tag (e.g. `v27.8.0`). Used to update builder references on main.

#### A5: Update .gitlab-ci.yml builder refs

Replace all `ref: v<OLD_VERSION>` lines for the `redhat/rhel-ai/wheels/builder` project includes with the latest builder tag from A4.

#### A6: Update builder-image-version.yml

Update `BUILDER_IMAGE_VERSION` variable to the latest builder tag from A4.

#### A7: Fetch current product-version.yml from main

```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Frhaiis%2Fpipeline/repository/files/product-version.yml?ref=main" | \
  jq -r '.content' | base64 -d
```

#### A8: Update PRODUCT_VERSION

Change the `PRODUCT_VERSION` value to `NEXT_VERSION`.

#### A9: Create MR with all changes

1. Locate or clone the pipeline repo (check workspace first)
2. Create feature branch from latest main
3. Apply all changes (renovate.json, product-version.yml, .gitlab-ci.yml, builder-image-version.yml)
4. Stage all changed files
5. Commit with AIPCC format, push, and create MR targeting `main` (use the `aipcc-commit` skill with `--push`)
6. Add comment to Step 5 and Step 6 JIRA stories with the MR link
7. Inform the user: Midstream team needs to approve and merge

### Part B: Containers Repo (Step 7)

#### B1: Fetch current renovate.json from containers main

```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/repository/files/renovate.json?ref=main" | \
  jq -r '.content' | base64 -d
```

#### B2: Check if rule already exists

Check if a base image version rule for the `RELEASE_BRANCH` already exists. If so, inform the user that Step 7 is done and transition to "Closed" (id: 61).

#### B3: Generate and create MR (if rule doesn't exist)

1. Locate or clone the containers repo (check workspace first)
2. Create feature branch from latest main
3. Add the new base image version rule to `renovate.json`, following existing patterns
4. Stage the changed file
5. Commit with AIPCC format, push, and create MR targeting `main` (use the `aipcc-commit` skill with `--push`)
6. Add comment to Step 7 JIRA story with the MR link
7. Inform the user: Midstream team needs to approve and merge

### Cleanup

- Summarize: MRs created for pipeline and containers, JIRA stories updated
- Transition completed stories to "Closed" (id: 61) once MRs are confirmed created

## Examples

### Update Renovate for a release
```bash
/rhaiis:release-renovate INFERENG-4584 3.3 3.4EA1
```

## Arguments

- **epic-key** (required): JIRA epic key for the release prep epic
  - Example: `INFERENG-4584`

- **release-branch** (required): The just-created release branch
  - Example: `3.3`

- **next-version** (required): The upcoming PRODUCT_VERSION
  - Example: `3.4EA1`

## See Also
- **`/rhaiis:release-branch`** - Create release branches
- **`/rhaiis:release-infra`** - Add infrastructure version entry
- **`/rhaiis:release-packages`** - Identify package changes between versions
