---
description: Release a vLLM container image to quay.io/vllm
argument-hint: <tag> <device>
---

## Name
odh-ai-helpers:release-vllm-midstream-image

## Synopsis
```
/release:vllm-midstream-image v0.14.0+rhai3 cuda  # Release CUDA image
/release:vllm-midstream-image v0.14.0+rhai3 rocm  # Release ROCm image
/release:vllm-midstream-image v0.14.0+rhai3 cpu   # Release CPU image
```

## Description
Triggers a GitHub Actions workflow to build and release a vLLM container image to quay.io/vllm. This command handles the nm-cicd workflow invocation with proper parameters for each hardware target.

**Supported hardware targets:**

| Target Device | Build Runner | Image Destination |
|---------------|--------------|-------------------|
| `cuda` | `ibm-wdc-k8s-a100-build-12-9` | `quay.io/vllm/vllm-cuda` |
| `rocm` | `os-mi300x-build-ubi-rocm64` | `quay.io/vllm/vllm-rocm` |
| `tpu` | `tpu-2x2` | `quay.io/vllm/vllm-tpu` |
| `cpu` | `rdu4-k8s-cpu` | `quay.io/vllm/vllm-cpu` |
| `neuron` | `rdu4-k8s-cpu` | `quay.io/vllm/vllm-neuron` |

## Implementation

### Step 1: Gather Parameters

Ask the user for:
1. **Tag** - Which tag to build (must include `v` prefix, e.g., `v0.14.0+rhai3`)
2. **Target device** - Which hardware target (cuda, rocm, tpu, cpu, neuron)

### Step 2: List Available Tags

Show recent tags from nm-vllm-ent:
```bash
gh api repos/neuralmagic/nm-vllm-ent/tags --jq '.[].name' | head -15
```

### Step 3: Validate Quay Repository

Check if the Quay repository exists:
```bash
curl -s "https://quay.io/api/v1/repository/vllm/vllm-<device>" | jq -r '.name // "NOT_FOUND"'
```

**If `NOT_FOUND`**, inform the user they need to complete these manual steps:
1. Get org access: Request membership at https://quay.io/organization/vllm
2. Create the repo: Go to https://quay.io/new/ and create `vllm/vllm-<device>`
3. Grant robot access:
   - Go to https://quay.io/organization/vllm?tab=robots
   - Click on the `vllm+cicd` robot account
   - Add **write** permissions for the new repository

### Step 4: Run the Workflow

Trigger the build workflow:
```bash
gh workflow run build-whl-image.yml --repo neuralmagic/nm-cicd --ref=main \
  -f wf_category=RELEASE \
  -f repo=neuralmagic/nm-vllm-ent \
  -f branch=<TAG> \
  -f python=3.12 \
  -f build_label=<BUILD_LABEL> \
  -f image_label=ibm-wdc-k8s-a100-dind \
  -f target_device=<TARGET_DEVICE> \
  -f release_image=true
```

**Build labels by device:**
- `cuda` → `ibm-wdc-k8s-a100-build-12-9`
- `rocm` → `os-mi300x-build-ubi-rocm64`
- `tpu` → `tpu-2x2`
- `cpu` → `rdu4-k8s-cpu`
- `neuron` → `rdu4-k8s-cpu`

### Step 5: Monitor the Workflow

Get the run ID and watch progress:
```bash
gh run list --repo neuralmagic/nm-cicd --workflow build-whl-image.yml --limit 3 \
  --json databaseId,displayTitle,status,conclusion
```

Watch the run:
```bash
gh run watch <run_id> --repo neuralmagic/nm-cicd
```

### Step 6: Verify Release

Once complete, confirm the image tag exists:
```bash
curl -s "https://quay.io/api/v1/repository/vllm/vllm-<device>/tag/?specificTag=<version>" | jq '.tags[0].name'
```

**Note:** Replace `+` with `_` in the tag name for quay.io queries (e.g., `v0.14.0_rhai3`).

## Examples

### Release CUDA image
```bash
/release:vllm-midstream-image v0.14.0+rhai3 cuda
```

### Release ROCm image
```bash
/release:vllm-midstream-image v0.14.0+rhai3 rocm
```

### Release CPU image
```bash
/release:vllm-midstream-image v0.14.0+rhai3 cpu
```

## Arguments

- **tag** (required): The nm-vllm-ent tag to build
  - Must include `v` prefix (e.g., `v0.14.0+rhai3`)
  - Must exist in neuralmagic/nm-vllm-ent

- **device** (required): Target hardware platform
  - Options: `cuda`, `rocm`, `tpu`, `cpu`, `neuron`

## Workflow Details

The `build-whl-image.yml` workflow in `neuralmagic/nm-cicd`:
1. Checks out the specified tag from nm-vllm-ent
2. Builds wheels for Python 3.12
3. Builds container image for the target device
4. Pushes to `quay.io/vllm/vllm-<device>:<tag>`

**Requirements:**
- GitHub CLI (`gh`) authenticated with access to neuralmagic repos
- Repository secrets configured in nm-cicd for Quay.io push

## See Also
- **`/downstream:release-status`** – Check overall release status
- nm-vllm-ent tags: https://github.com/neuralmagic/nm-vllm-ent/tags
- nm-cicd workflows: https://github.com/neuralmagic/nm-cicd/actions
