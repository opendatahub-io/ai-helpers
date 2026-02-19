---
description: Identify package changes between vLLM versions and create AIPCC JIRA issues
argument-hint: <epic-key> <old-version> <new-version>
---

## Name
odh-ai-helpers:rhaiis-release-packages

## Synopsis
```
/rhaiis:release-packages INFERENG-4584 v0.12.0+rhai5 v0.13.0+rhai1
```

## Description
Automates **Step 1** of RHAIIS release preparation: identifying package differences between vLLM versions and creating AIPCC JIRA issues for packages that need attention.

Runs the `rhaiis-img-spec-prep.yml` workflow in `neuralmagic/nm-cicd` to generate a package diff, then creates JIRA issues in the AIPCC project for new or changed packages requiring review.

**JIRA transitions:** In Progress = `41`, Closed = `61`

## Implementation

### Step 0: Gather Parameters

Ask the user for:
1. **EPIC_KEY** - The release prep epic key (e.g. `INFERENG-4584`)
2. **OLD_VLLM_VERSION** - The previous vLLM version tag (e.g. `v0.12.0+rhai5`)
3. **NEW_VLLM_VERSION** - The new vLLM version tag (e.g. `v0.13.0+rhai1`)

### Step 1: Find and Transition JIRA Story

Search for child stories under the epic (`"Epic Link" = <EPIC_KEY>`).

Find the **Step 1 story**: Summary contains "Step 1:" (package identification).

Transition it to "In Progress" (id: 41).

### Step 2: Run the Package Diff Workflow

Trigger the `rhaiis-img-spec-prep.yml` workflow:
```bash
gh workflow run rhaiis-img-spec-prep.yml --repo neuralmagic/nm-cicd --ref main \
  -f old_version="<OLD_VLLM_VERSION>" \
  -f new_version="<NEW_VLLM_VERSION>"
```

### Step 3: Monitor the Workflow

Get the run ID and watch progress:
```bash
gh run list --repo neuralmagic/nm-cicd --workflow rhaiis-img-spec-prep.yml --limit 3 \
  --json databaseId,displayTitle,status,conclusion
```

```bash
gh run watch <run_id> --repo neuralmagic/nm-cicd
```

### Step 4: Fetch and Display Results

Once the workflow completes, fetch the package diff output:
```bash
gh run view <run_id> --repo neuralmagic/nm-cicd --log | grep -A 1000 "Package Diff"
```

Display the results in a clear table format showing:
- New packages added
- Packages removed
- Packages with version changes
- Packages needing AIPCC attention (new dependencies, license changes, etc.)

### Step 5: Create AIPCC JIRA Issues

For packages that need AIPCC attention (new packages, significant version bumps, license changes), create JIRA issues in the AIPCC project.

Each issue should be modeled as a clone of AIPCC-1 (the template issue for package requests):

1. Create the issue with:
   - **Project**: AIPCC
   - **Summary**: `Package request: <package_name> <version>`
   - **Description**: Include the package name, version, why it's needed (new dependency for vLLM `<NEW_VLLM_VERSION>`), and any relevant license information

2. Present all proposed issues to the user for confirmation before creating them.

### Step 6: Update JIRA Story

Add a comment to the Step 1 JIRA story with:
- Summary of package diff results (counts: added, removed, changed)
- Links to any created AIPCC issues
- Workflow run link: `https://github.com/neuralmagic/nm-cicd/actions/runs/<run_id>`

### Step 7: Complete

Transition the Step 1 story to "Closed" (id: 61).

Summarize to the user:
- Package diff results
- Number of AIPCC issues created (with links)
- Step 1 JIRA story updated and closed

## Examples

### Run package diff
```bash
/rhaiis:release-packages INFERENG-4584 v0.12.0+rhai5 v0.13.0+rhai1
```

## Arguments

- **epic-key** (required): JIRA epic key for the release prep epic
  - Example: `INFERENG-4584`

- **old-version** (required): Previous vLLM version tag
  - Example: `v0.12.0+rhai5`

- **new-version** (required): New vLLM version tag
  - Example: `v0.13.0+rhai1`

## See Also
- **`/rhaiis:release-branch`** - Create release branches
- **`/rhaiis:release-infra`** - Add infrastructure version entry
- **`/rhaiis:release-renovate`** - Update Renovate configs for release
