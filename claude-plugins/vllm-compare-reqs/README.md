# vLLM Compare Requirements Plugin

Compare vllm requirements files **and Dockerfiles** between versions to identify dependency changes for AIPCC package onboarding workflows.

**For accelerator builds** (ROCm, CUDA, CPU, TPU, XPU), Dockerfile comparison is critical because they specify exact commits/branches for dependencies built from source (PyTorch, Triton, Flash Attention, etc.) - information not available in requirements files.

**Note:** Each variant compares only the files that actually exist in the vllm repository. For example, CUDA has `cuda.txt` but no `cuda-build.txt`, while ROCm has both `rocm.txt` and `rocm-build.txt`.

## Installation

```bash
/plugin install vllm-compare-reqs@odh-ai-helpers
```

## Commands

### `/vllm-compare-reqs:compare`

Intelligent comparison tool that analyzes vllm requirements files between versions and provides actionable insights for AIPCC workflows.

**Usage:**
```bash
/vllm-compare-reqs:compare v0.13.0 v0.14.0 rocm                         # ROCm runtime + build + Dockerfiles
/vllm-compare-reqs:compare v0.13.0 v0.14.0 cuda                         # CUDA runtime + build + Dockerfiles
/vllm-compare-reqs:compare v0.13.0 v0.14.0 docker/Dockerfile.rocm_base  # Specific Dockerfile
/vllm-compare-reqs:compare v0.13.0 v0.14.0 common.txt                   # Specific requirements file
```

**Also available as a skill:** `/vllm-compare-reqs` (same functionality, no colon)

**Features:**
- ✅ **Variant mode**: Automatically compares runtime + build requirements **+ Dockerfiles** (rocm/cuda)
- ✅ **Dockerfile analysis**: Compares ARG statements (base images, build commits) for ROCm/CUDA
- ✅ **Summary table**: Quick overview of all changes at a glance
- ✅ **Clean output**: Categorized changes (📦 Changed, ➕ Added, ➖ Removed)
- ✅ **Impact analysis**: AI provides actionable insights for package onboarding
- ✅ **No dependencies**: Pure Python using standard library only

**Supported variants:** `rocm`, `cuda`, `cpu`, `tpu`, `xpu` (Intel GPU)

## Use Cases

### Package Onboarding
Identify new packages that need onboarding before upgrading vllm versions:
- Extract purpose from requirement comments
- Assess complexity (pure Python vs compiled)
- Prioritize onboarding work

### Debugging Build Failures
Correlate requirement changes with build errors:
- Identify missing or mismatched dependencies
- Recommend specific package versions

### Release Planning
Estimate effort for vllm upgrades:
- Count new packages requiring onboarding
- Identify breaking changes
- Generate timeline and action plan

## Output Example

```
=== Comparing rocm variant (build): v0.13.0 -> v0.14.0rc1 ===

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 common.txt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Changed:
  xgrammar == 0.1.27 → xgrammar == 0.1.29
  mistral_common[image] >= 1.8.5 → mistral_common[image] >= 1.8.8

➕ Added:
  grpcio>=1.76.0

➖ Removed:
  scipy # Required for phi-4-multimodal-instruct

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 rocm-build.txt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Changed:
  torch==2.9.0 → torch==2.9.1
  triton==3.5.0 → triton==3.5.1
```

The AI then provides intelligent impact analysis with:
- Overall impact level (Low/Medium/High)
- Packages requiring onboarding
- Breaking changes
- Concrete next steps

## AIPCC Workflow Integration

This plugin is specifically designed for AIPCC (AI Portfolio Component Collection) workflows:

- **Package Onboarding**: Streamlines identifying dependencies for the wheels builder
- **Build Configuration**: Helps maintain proper dependency versions across hardware variants
- **Release Management**: Assists in planning vllm upgrades and estimating work

## Technical Details

- **Language**: Python 3 (standard library only)
- **Network**: Fetches files directly from vllm GitHub repository
- **Platform**: Cross-platform compatible
- **Output**: Colored terminal output with emoji indicators

## See Also

- [vllm GitHub Repository](https://github.com/vllm-project/vllm)
- [AIPCC Wheels Builder](https://github.com/opendatahub-io/wheels-builder)
- [Fromager Documentation](https://fromager.readthedocs.io/)

