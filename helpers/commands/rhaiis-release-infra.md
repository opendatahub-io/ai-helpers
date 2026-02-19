---
description: Add infrastructure version entry for a new RHAIIS release
argument-hint: <epic-key> <version>
---

## Name
odh-ai-helpers:rhaiis-release-infra

## Synopsis
```
/rhaiis:release-infra INFERENG-4584 3.4-ea1  # Add version entry for 3.4-ea1
```

## Description
Automates **Step 4** of RHAIIS release preparation: adding a new version entry to the infrastructure product configuration in `core/infrastructure`.

**GitLab repository:**

| Repository | Encoded Path |
|------------|-------------|
| `core/infrastructure` | `redhat%2Frhel-ai%2Fcore%2Finfrastructure` |

**JIRA transitions:** In Progress = `41`, Closed = `61`

## Implementation

### Step 0: Gather Parameters

Ask the user for:
1. **EPIC_KEY** - The release prep epic key (e.g. `INFERENG-4584`)
2. **NEW_VERSION** - The upcoming release version (e.g. `3.4-ea1`)

### Step 1: Find JIRA Story

Search for child stories under the epic (`"Epic Link" = <EPIC_KEY>`).

Find the **Step 4 story**: Summary contains "Step 4:" (infrastructure version entry).

Transition it to "In Progress" (id: 41).

### Step 2: Fetch Current rhaiis.yml

```bash
glab api --hostname gitlab.com \
  "projects/redhat%2Frhel-ai%2Fcore%2Finfrastructure/repository/files/data%2Fproducts%2Frhaiis.yml?ref=main" | \
  jq -r '.content' | base64 -d
```

Study the existing version blocks to understand the structure and standard variants.

### Step 3: Generate New Version Block

Generate a new version block for `NEW_VERSION` by copying the variants from the most recent major version block in the file (e.g. the `3.3` block, not a patch release). This includes all collections (e.g. `rhaiis` and `model-opt`) and all their variants/architectures.

Follow the exact YAML structure of that version block. Present the generated block to the user for confirmation before proceeding.

### Step 4: Create MR

1. Locate the infrastructure repo (ask the user — it is likely already cloned in the workspace, e.g. `infrastructure/` directory). Only clone from `git@gitlab.com:redhat/rhel-ai/core/infrastructure.git` if not available locally.

2. Create feature branch from an up-to-date `main`:
   ```bash
   git -C <INFRA_REPO_PATH> checkout main && git -C <INFRA_REPO_PATH> pull
   git -C <INFRA_REPO_PATH> checkout -b "<STEP4_JIRA_TICKET>-add-<NEW_VERSION>-version"
   ```

3. Add the new version entry to `data/products/rhaiis.yml`. Insert it after the most recent major version block, maintaining the file's YAML structure.

4. Stage the changed file:
   ```bash
   git -C <INFRA_REPO_PATH> add data/products/rhaiis.yml
   ```

5. Commit with AIPCC format, push, and create MR targeting `main` (use the `aipcc-commit` skill with `--push`).

6. Add comment to Step 4 JIRA story with the MR link.

7. Inform the user: AIPCC team needs to approve and merge.

### Cleanup

Summarize: MR created, JIRA story updated with MR link.

## Examples

### Add version entry
```bash
/rhaiis:release-infra INFERENG-4584 3.4-ea1
```

## Arguments

- **epic-key** (required): JIRA epic key for the release prep epic
  - Example: `INFERENG-4584`

- **version** (required): The new version to add to the infrastructure config
  - Example: `3.4-ea1`

## See Also
- **`/rhaiis:release-branch`** - Create release branches
- **`/rhaiis:release-packages`** - Identify package changes between versions
- **`/rhaiis:release-renovate`** - Update Renovate configs for release
