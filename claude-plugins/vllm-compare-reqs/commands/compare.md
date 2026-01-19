# vllm Compare Requirements

Compare vllm requirements files and Dockerfiles between versions to identify dependency changes.

## Usage

When the user invokes this command with version arguments and a variant or specific file:

```
/vllm:compare-reqs v0.13.0 v0.14.0 rocm
/vllm:compare-reqs v0.13.0 v0.14.0rc1 cuda
/vllm:compare-reqs v0.13.0 v0.14.0 common.txt
/vllm:compare-reqs v0.13.0 v0.14.0 docker/Dockerfile.rocm
```

## Steps

1. **Find and run the comparison script**:
   - First, search for the script file: `**/compare_reqs.py`
   - Then execute it with Python using its absolute path:
     ```bash
     python3 /path/to/compare_reqs.py <version1> <version2> <variant_or_file> --pretty
     ```
   - Always use the `--pretty` flag for cleaner output unless user explicitly requests raw diff

2. **Present the results** showing:
   - Summary table of all changes (packages, versions, change types)
   - Detailed categorized changes per file (Changed, Added, Removed, Infrastructure)
   - URLs compared for verification

3. **Provide intelligent analysis** including:
   - **Impact Assessment**: Categorize as low/medium/high impact
   - **Action Required**: New packages to onboard, version updates needed
   - **Breaking Changes**: Major version bumps, removed dependencies
   - **Package Onboarding Impact**: For each new package, explain purpose, complexity, and provide PyPI link
   - **Dockerfile Analysis**: Explain significance of ARG changes (base image, build commits, new libraries)
   - **Next Steps**: Concrete action items for the user
   - **Context**: Infer the purpose of the update if possible

## Variants and Files

**Variants** (auto-include runtime + build requirements + Dockerfiles):
- `rocm`: common.txt, rocm.txt, rocm-build.txt, Dockerfile.rocm, Dockerfile.rocm_base
- `cuda`: common.txt, cuda.txt, Dockerfile
- `cpu`: common.txt, cpu.txt, cpu-build.txt, Dockerfile.cpu
- `tpu`: common.txt, tpu.txt, Dockerfile.tpu
- `xpu`: common.txt, xpu.txt, Dockerfile.xpu

**Specific files**: Any requirements file (e.g., `common.txt`, `rocm-build.txt`) or Dockerfile (e.g., `docker/Dockerfile.rocm`)

## Expected Output Format

The script provides:
1. **Summary Table**: All changes in tabular format (File, Package, Old Version, New Version, Type)
2. **Detailed Changes**: Per-file breakdown with emoji indicators:
   - 📦 Changed packages/ARGs
   - ➕ Added packages/ARGs
   - ➖ Removed packages/ARGs
   - 🔧 Infrastructure changes (URLs, etc.)
3. **URLs Compared**: Direct links to GitHub for verification

## Analysis Guidelines

After displaying the comparison output, provide actionable insights:

### Impact Assessment
Categorize the overall impact based on:
- Number of new packages requiring onboarding
- Major vs minor version changes
- Removed dependencies
- Infrastructure changes (base images, build commits)

### Actionable Sections
Structure your analysis with:
- ✅ **No Action Required**: Unchanged critical dependencies
- ⚠️ **Action Required**: New packages, updates, investigations needed
- 🚨 **Breaking Changes**: Major version bumps or removed packages

### Package Onboarding Impact
For each new package identified:
- Purpose (inferred from comments in requirements file)
- Likely build complexity (pure Python vs compiled extensions)
- PyPI link: `https://pypi.org/project/package-name/`
- Any ambiguity or special considerations

### Dockerfile Analysis
For Dockerfile ARG changes:
- Explain the significance (e.g., base image change, new PyTorch commit)
- Identify new dependencies being built from source
- Recommend actions (update build configs, verify commits exist)

### Next Steps
Provide concrete, prioritized action items:
1. Package onboarding commands
2. Build verification steps
3. Investigation areas
4. Testing recommendations

### Context Inference
Based on the changes, infer:
- The purpose of the update (new features, bug fixes, performance improvements)
- Related GitHub issues or release notes if patterns emerge
- Potential risks or compatibility concerns

## Example Analysis Structure

```
## Summary of Changes: vllm v0.13.0 → v0.14.0 (ROCm Variant)

### Impact Level: **Medium-High**

## 📊 Change Analysis

### ✅ No Action Required:
- Core framework packages remain stable
- No breaking changes in pytorch ecosystem

### ⚠️ Action Required:
1. **New package: `grpcio>=1.76.0`**
   - Purpose: gRPC support for LlamaTokenizer
   - Complexity: C extension (requires compilation)
   - PyPI: https://pypi.org/project/grpcio/
   
2. **Updated: `torch` 2.9.0 → 2.9.1**
   - Patch update, likely straightforward

### 🚨 Critical Infrastructure Changes:
**BASE_IMAGE downgrade**: rocm/dev-ubuntu-22.04:7.1 → 7.0
- Unusual downgrade suggests 7.1 compatibility issues
- Investigate vllm issue tracker for ROCm 7.1 problems

## 🎯 Next Steps:
1. Onboard grpcio packages (in dependency order)
2. Verify ROCm 7.0 compatibility
3. Update torch/torchvision/torchaudio
4. Test new distributed training libraries

## 🔍 Context:
This release focuses on gRPC infrastructure and distributed training enhancements for multi-GPU ROCm setups.
```

