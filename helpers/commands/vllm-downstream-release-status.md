---
description: Check RHAIIS downstream release status and suggest next steps
argument-hint: <version> [accelerator]
---

## Name
odh-ai-helpers:vllm-downstream-release-status

## Synopsis
```
/vllm:downstream-release-status v0.14.0+rhai3      # Check specific release
/vllm:downstream-release-status v0.14.0+rhai3 cuda # Check specific accelerator
/vllm:downstream-release-status v0.14.0 all        # Check all accelerators
```

## Description
Checks the status of a downstream RHAIIS (Red Hat AI Inference Server) release across all constituent repositories and pipelines. Provides a comprehensive status report and suggests the next action needed.

**Repositories tracked:**
- `neuralmagic/nm-vllm-ent` (GitHub) - Source vLLM with Red Hat patches
- `redhat/rhel-ai/core/base-images/app` (GitLab) - Base container images
- `redhat/rhel-ai/rhaiis/pipeline` (GitLab) - Wheel build pipeline
- `redhat/rhel-ai/rhaiis/containers` (GitLab) - Container image build

**Accelerators supported:** cpu, cuda, rocm, tpu, spyre, neuron

## Implementation

### Release Workflow Overview

```
nm-vllm-ent (GitHub)     →  Merge PR  →  Create tag (v0.X.Y+rhaiZ)
        ↓ (mirrored to GitLab)
rhaiis/pipeline (GitLab) →  Renovate detects new tag  →  Creates MR  →  Build wheels
        ↓ (Renovate propagates)
rhaiis/containers (GitLab) →  Renovate updates wheel refs  →  Merge  →  Create tag

                    ↑ (base images also flow into containers)
base-images/app (GitLab) →  Merge MR  →  Build base images  →  Renovate updates containers
```

### Step 1: Gather Parameters

Ask the user for:
1. **Version** - Which release to check (e.g., `v0.14.0+rhai3`)
2. **Accelerator** - Which hardware target (cuda, rocm, tpu, cpu, spyre, or all)

### Step 2: Check nm-vllm-ent Status (GitHub)

Check if the tag exists:
```bash
gh api repos/neuralmagic/nm-vllm-ent/tags --jq '.[].name' | grep -E "^v[0-9]+\.[0-9]+\.[0-9]+" | head -10
```

Check for open PRs:
```bash
gh api repos/neuralmagic/nm-vllm-ent/pulls --jq '.[] | "\(.number): \(.title) [\(.state)]"' | head -10
```

### Step 3: Check rhaiis/pipeline Status (GitLab)

List open MRs:
```bash
glab mr list -R redhat/rhel-ai/rhaiis/pipeline -A --per-page 20 -F json | jq -r '.[] | "\(.iid): \(.title) [\(.state)]"'
```

Get MR details:
```bash
glab mr view <MR_IID> -R redhat/rhel-ai/rhaiis/pipeline -F json | jq '{title, state, web_url}'
```

Check pipeline status:
```bash
glab ci list -R redhat/rhel-ai/rhaiis/pipeline --per-page 5
```

### Step 4: Check base-images/app Status (GitLab)

Search for related MRs:
```bash
glab mr list -R redhat/rhel-ai/core/base-images/app -A --per-page 15 -F json | jq -r '.[] | "\(.iid): \(.title) [\(.state)]"'
```

Check current base image version in containers:
```bash
glab api --hostname gitlab.com "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/repository/files/build-args%2F<accel>-ubi9.conf?ref=main" | jq -r '.content' | base64 -d | grep BASE_IMAGE
```

### Step 5: Check rhaiis/containers Status (GitLab)

**CRITICAL: Check actual branch state first**

```bash
# Check all accelerator configs in the target branch
for accel in cpu cuda rocm tpu spyre neuron; do
  echo "=== $accel ==="
  glab api --hostname gitlab.com "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/repository/files/build-args%2F${accel}-ubi9.conf?ref=<BRANCH>" 2>/dev/null | jq -r '.content' | base64 -d | grep -E "^(BASE_IMAGE|WHEEL_RELEASE)"
done
```

Check recently merged MRs:
```bash
glab api --hostname gitlab.com "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/merge_requests?state=merged&target_branch=<BRANCH>&per_page=10" | jq -r '.[] | "\(.iid): \(.title) [\(.merged_at)]"'
```

List open MRs:
```bash
glab api --hostname gitlab.com "projects/redhat%2Frhel-ai%2Frhaiis%2Fcontainers/merge_requests?state=opened&per_page=20" | jq -r '.[] | "\(.iid): \(.title) [\(.target_branch)]"'
```

### Step 6: Check Konflux Pipeline Status

Get the tag pipeline SHA:
```bash
glab api --hostname gitlab.com "projects/redhat%2Frhel-ai%2Fcore%2Fbase-images%2Fapp/pipelines?per_page=5" | jq '[.[] | select(.ref | startswith("v"))][0] | {id, status, ref, sha, web_url}'
```

Check Konflux build statuses:
```bash
glab api --hostname gitlab.com "projects/redhat%2Frhel-ai%2Fcore%2Fbase-images%2Fapp/repository/commits/<SHA>/statuses?per_page=50" | jq '.[] | select(.name | contains("Konflux Production Internal")) | {name, status, target_url}'
```

### Step 7: Generate Status Report

Create a summary table:

```
## Release Status: <version>
## Accelerator: <accelerator(s)>

| Stage | Status | Details |
|-------|--------|---------|
| nm-vllm-ent Tag | ✅/❌ | Tag exists at github.com/neuralmagic/nm-vllm-ent |
| Pipeline Renovate MR | ✅ Merged / ⏳ Open !XXX / ❌ Not created | [link] |
| Pipeline Wheels | ✅ Published / ⏳ Building / ❌ Failed | [pipeline link] |
| Base Image MR | ✅ Merged / ⏳ Open !XXX / ➖ Not needed | [link if applicable] |
| Containers Renovate MR | ✅ Merged / ⏳ Open !XXX / ❌ Waiting | [link] |

### Per-Accelerator Status

| Accelerator | Base Image | Wheels | Status |
|-------------|------------|--------|--------|
| cpu | `3.3.0-XXXXXXXX` | `3.3.XXXX` | ✅/⏳ |
| cuda | `3.3.0-XXXXXXXX` | `3.3.XXXX` | ✅/⏳ |
```

### Step 8: Suggest Next Action

Based on findings, recommend ONE of:
1. **Tag missing**: "Create tag in nm-vllm-ent"
2. **Waiting for Renovate**: "Renovate should detect within ~1 hour"
3. **Pipeline MR open**: "Review and merge pipeline MR !XXX"
4. **Waiting for wheels**: "Pipeline building wheels, wait for completion"
5. **Base image not merged**: "Merge base-images MR !XXX first"
6. **Base image not propagated**: "Wait for Konflux release + Renovate"
7. **Ready to merge containers**: "Merge containers MRs, then create tag"
8. **Ready for container tag**: "Create tag in rhaiis/containers"

## Examples

### Check specific release
```bash
/vllm:downstream-release-status v0.14.0+rhai3
```

### Check CUDA specifically
```bash
/vllm:downstream-release-status v0.14.0+rhai3 cuda
```

### Full status for all accelerators
```bash
/vllm:downstream-release-status v0.14.0 all
```

## Arguments

- **version** (required): Release version to check (e.g., `v0.14.0+rhai3`)
- **accelerator** (optional): Hardware target to check
  - Options: `cpu`, `cuda`, `rocm`, `tpu`, `spyre`, `neuron`, `all`
  - Default: Asks user to specify

## Reference Links

- nm-vllm-ent tags: https://github.com/neuralmagic/nm-vllm-ent/tags
- Base images MRs: https://gitlab.com/redhat/rhel-ai/core/base-images/app/-/merge_requests
- Pipeline MRs: https://gitlab.com/redhat/rhel-ai/rhaiis/pipeline/-/merge_requests
- Containers MRs: https://gitlab.com/redhat/rhel-ai/rhaiis/containers/-/merge_requests
- Konflux UI: https://konflux-ui.apps.stone-prod-p02.hjvn.p1.openshiftapps.com/ns/ai-tenant/applications

## See Also
- **`/vllm:release-midstream-image`** – Release a vLLM container image to quay.io
