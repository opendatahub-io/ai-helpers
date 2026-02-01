---
name: vllm-compare-reqs
description: Compare vllm requirements files between versions
allowed-tools: Bash
user-invocable: true
---

# vllm Compare Requirements Skill

## Purpose

Compare vllm requirements files **and Dockerfiles** between versions to identify dependency changes, providing intelligent analysis for AIPCC package onboarding workflows.

**For accelerator builds** (ROCm, CUDA, TPU, XPU), Dockerfile comparison is critical because they specify exact commits/branches for dependencies built from source (PyTorch, Triton, Flash Attention, etc.) - information not available in requirements files.

**Note:** Each variant compares only the files that actually exist in the vllm repository. For example, CUDA has `cuda.txt` but no `cuda-build.txt`, while ROCm has both `rocm.txt` and `rocm-build.txt`.

## Skill Type

**Executable Script** - Runs a Python script to fetch and compare requirements files from the vllm GitHub repository.

## When to Use

Use this skill when you need to:
- Compare vllm runtime AND build requirements between versions before upgrading
- Identify new packages that need onboarding to the AIPCC wheels builder
- Understand dependency changes for specific hardware variants (ROCm, CUDA, etc.)
- **Analyze Dockerfile ARG changes** (build commits/branches for ROCm/CUDA)
- Debug build failures related to dependency mismatches

**Note:** Variant comparisons include BOTH runtime and build dependencies to ensure complete coverage.

## Usage

### Basic Syntax

```bash
./scripts/compare_reqs.py <version1> <version2> <variant|file> [--pretty]
```

### Arguments

- **version1**: First version to compare (e.g., `v0.13.0`, `v0.14.0rc1`)
- **version2**: Second version to compare
- **variant|file**: Either:
  - Variant name: `rocm`, `cuda`, `cpu`, `tpu`, `xpu` (auto-includes runtime + build requirements + Dockerfiles)
  - Specific file: `rocm-build.txt`, `common.txt`, `docker/Dockerfile.rocm`, etc.
- **--pretty**: Show clean categorized output (default)
- **--no-pretty**: Show simple diff output

### Examples

```bash
# Compare ROCm runtime + build requirements + Dockerfiles
./scripts/compare_reqs.py v0.13.0 v0.14.0 rocm

# Compare CUDA runtime + build requirements + Dockerfiles
./scripts/compare_reqs.py v0.13.0 v0.14.0 cuda

# Compare specific file only
./scripts/compare_reqs.py v0.13.0 v0.14.0 common.txt
./scripts/compare_reqs.py v0.13.0 v0.14.0 rocm-build.txt
./scripts/compare_reqs.py v0.13.0 v0.14.0 docker/Dockerfile.rocm_base

# All variants (based on what files actually exist in vllm repo)
./scripts/compare_reqs.py v0.13.0 v0.14.0 rocm   # common.txt + rocm.txt + rocm-build.txt + Dockerfiles
./scripts/compare_reqs.py v0.13.0 v0.14.0 cuda   # common.txt + cuda.txt + Dockerfile
./scripts/compare_reqs.py v0.13.0 v0.14.0 cpu    # common.txt + cpu.txt + cpu-build.txt + Dockerfile.cpu
./scripts/compare_reqs.py v0.13.0 v0.14.0 tpu    # common.txt + tpu.txt + Dockerfile.tpu
./scripts/compare_reqs.py v0.13.0 v0.14.0 xpu    # common.txt + xpu.txt + Dockerfile.xpu (Intel GPU)
```

## Output Format

The script provides clean, categorized output with a **summary table** followed by detailed changes:

```
=== Comparing rocm variant (build + Dockerfiles): v0.13.0 -> v0.14.0rc1 ===

📊 Change Summary Table:

File                 Package                             Old Version               New Version               Type      
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
common.txt           protobuf                            -                         >= 6.30.0                 Added
common.txt           grpcio                              -                         >=1.76.0                  Added
rocm-build.txt       torch                               ==2.9.0                   ==2.9.1                   Changed
rocm-build.txt       triton                              ==3.5.0                   ==3.5.1                   Changed
docker/Dockerfil...  PYTORCH_BRANCH=1c57644d                                                                 Changed
docker/Dockerfil...  MORI_BRANCH=2d02c6a9                -                                                   Added

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 common.txt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Changed:
  xgrammar == 0.1.27 → xgrammar == 0.1.29
  mistral_common[image] >= 1.8.5 → mistral_common[image] >= 1.8.8

➕ Added:
  protobuf >= 6.30.0 # Required by LlamaTokenizer, gRPC.
  grpcio>=1.76.0

➖ Removed:
  scipy # Required for phi-4-multimodal-instruct

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 rocm-build.txt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Changed:
  torch==2.9.0 → torch==2.9.1
  triton==3.5.0 → triton==3.5.1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐳 docker/Dockerfile.rocm_base
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Changed:
  BASE_IMAGE=rocm/dev-ubuntu-22.04:7.1-complete → BASE_IMAGE=rocm/dev-ubuntu-22.04:7.0-complete
  PYTORCH_BRANCH=1c57644d → PYTORCH_BRANCH=89075173
  AITER_BRANCH=59bd8ff2 → AITER_BRANCH=6af8b687

➕ Added:
  MORI_BRANCH=2d02c6a9
  MORI_REPO=https://github.com/ROCm/mori.git
  RIXL_BRANCH=50d63d94
  RIXL_REPO=https://github.com/vcave/RIXL.git
```

## AI Analysis Requirements

After running the script and displaying the output, **you must provide intelligent impact analysis**:

### Required Analysis Sections

1. **Summary**: Brief overview of changes
2. **Impact Level**: Low/Medium/High based on:
   - Number of new packages
   - Breaking changes (major version bumps)
   - Removed dependencies
   - **Dockerfile ARG changes** (especially BASE_IMAGE, PYTORCH_BRANCH, etc.)
3. **AIPCC Wheels Builder Impact**:
   - ✅ No Action Required: Stable dependencies
   - ⚠️ Action Required: New packages to onboard, version updates
   - 🚨 Breaking Changes: Major issues, base image changes
4. **Package Details**: For each new package:
   - Purpose (from requirement comments)
   - Complexity assessment (pure Python vs compiled)
   - PyPI link
   - Any ambiguities (multiple packages with same name)
5. **Dockerfile Analysis** (for ROCm/CUDA):
   - Base image changes (ROCm/CUDA version changes)
   - Source build commit changes (PyTorch, Triton, etc.)
   - New dependencies added (MORI, RIXL, UCX, etc.)
6. **Next Steps**: Concrete action items
7. **Context**: Infer purpose of the update

### Example Analysis

```markdown
## Summary of Changes: vllm v0.13.0 → v0.14.0rc1

### Impact Level: Medium

### AIPCC Wheels Builder Impact:

#### ✅ No Action Required:
- ROCm version remains at 6.4
- PyTorch ecosystem stable (minor patch updates only)

#### ⚠️ Action Required:
**New packages to onboard:**
1. **`grpcio>=1.76.0`** (NEW)
   - Purpose: gRPC support
   - Complexity: Compiled extension (C++)
   - PyPI: https://pypi.org/project/grpcio/
   - Action: Onboard grpcio 1.76.0+

**Version updates:**
- torch: 2.9.0 → 2.9.1 (patch - safe)
- triton: 3.5.0 → 3.5.1 (patch - safe)

**Removed dependencies:**
- scipy: Was required for phi-4-multimodal-instruct
  - Risk: Low (model-specific, may not be widely used)

#### Next Steps:
1. Onboard grpcio>=1.76.0 to wheels builder
2. Verify torch 2.9.1 and triton 3.5.1 availability
3. Test vllm 0.14.0rc1 build with new dependencies
4. Validate phi-4 model functionality without scipy

**Context:** This release adds gRPC support and updates to PyTorch 2.9.1.
```

## Integration with AIPCC Workflows

### Package Onboarding

When onboarding a new vllm version:
1. Run comparison to identify new dependencies
2. Analyze complexity of each new package
3. Prioritize onboarding based on impact
4. Generate action plan

### Debugging Build Failures

When builds fail:
1. Compare requirements between working and failing versions
2. Correlate changes with error messages
3. Identify missing or mismatched dependencies
4. Recommend fixes

### Release Planning

When planning releases:
1. Compare requirements across multiple versions
2. Estimate onboarding effort
3. Identify blocking dependencies
4. Generate timeline

## Technical Details

- **Language**: Python 3
- **Dependencies**: Standard library only (urllib)
- **Network**: Fetches files from GitHub (requires internet)
- **Colors**: Uses ANSI color codes for terminal output
- **Exit codes**: 0 for success, 1 for failure

## Error Handling

The script gracefully handles:
- Version not found (404 errors)
- File not found in specific version
- Network errors
- Invalid input

## See Also

- [vllm GitHub Repository](https://github.com/vllm-project/vllm)
- [AIPCC Package Onboarding Guide](../../../../../../builder/AGENTS.md)
- [Fromager Documentation](https://fromager.readthedocs.io/)

