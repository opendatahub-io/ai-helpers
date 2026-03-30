---
name: vllm-compare-reqs
description: "Compare vllm requirements files and Dockerfiles between versions to identify dependency changes for AIPCC package onboarding. Identifies added, removed, and changed packages across hardware variants (ROCm, CUDA, CPU, TPU, XPU) and analyzes Dockerfile ARG changes for source-built dependencies. Use when comparing vllm dependency diffs, reviewing version upgrades, debugging build failures from dependency mismatches, or planning AIPCC wheels builder onboarding."
allowed-tools: Bash
user-invocable: true
---

# vllm Compare Requirements

Compare vllm requirements files and Dockerfiles between versions to identify dependency changes for AIPCC package onboarding workflows.

For accelerator builds (ROCm, CUDA, TPU, XPU), Dockerfile comparison is critical — they specify exact commits/branches for dependencies built from source (PyTorch, Triton, Flash Attention) not available in requirements files.

## When to Use

- Compare vllm runtime and build requirements between versions before upgrading
- Identify new packages that need onboarding to the AIPCC wheels builder
- Analyze Dockerfile ARG changes (build commits/branches for ROCm/CUDA)
- Debug build failures related to dependency mismatches

## Usage

```bash
./scripts/compare_reqs.py <version1> <version2> <variant|file> [--pretty]
```

**Arguments:**
- **version1/version2**: Versions to compare (e.g., `v0.13.0`, `v0.14.0rc1`)
- **variant|file**: Variant name (`rocm`, `cuda`, `cpu`, `tpu`, `xpu`) which auto-includes runtime + build + Dockerfiles, or a specific file (`common.txt`, `rocm-build.txt`, `docker/Dockerfile.rocm`)
- **--no-pretty**: Show simple diff instead of categorized output

### Examples

```bash
# Compare full variant (runtime + build + Dockerfiles)
./scripts/compare_reqs.py v0.13.0 v0.14.0 rocm
./scripts/compare_reqs.py v0.13.0 v0.14.0 cuda

# Compare specific file only
./scripts/compare_reqs.py v0.13.0 v0.14.0 common.txt
./scripts/compare_reqs.py v0.13.0 v0.14.0 docker/Dockerfile.rocm_base
```

Each variant compares only files that exist in the vllm repo (e.g., CUDA has `cuda.txt` but no `cuda-build.txt`; ROCm has both).

## After Running the Script

Provide an impact analysis covering:

1. **Impact Level** (Low/Medium/High): based on new packages, breaking changes, removed deps, Dockerfile ARG changes
2. **AIPCC Wheels Builder Impact**: categorize as No Action / Action Required / Breaking Changes
3. **Package Details** for each new dependency: purpose, complexity (pure Python vs compiled), PyPI link
4. **Dockerfile Analysis** (ROCm/CUDA): base image changes, source build commit changes, new dependencies
5. **Next Steps**: concrete action items for onboarding

## See Also

- [vllm GitHub Repository](https://github.com/vllm-project/vllm)
- [Fromager Documentation](https://fromager.readthedocs.io/)
