---
description: Compare vllm requirements files and Dockerfiles between versions
argument-hint: <version1> <version2> <variant|requirements-file> [--pretty]
---

## Name
vllm-compare-reqs

## Synopsis
```
/vllm-compare-reqs <version1> <version2> <variant|requirements-file> [--pretty]
/vllm-compare-reqs v0.10.0 v0.13.0 rocm                         # Runtime + build + Dockerfiles
/vllm-compare-reqs v0.10.0 v0.13.0 rocm-build.txt               # Specific file only
/vllm-compare-reqs v0.10.0 v0.13.0 docker/Dockerfile.rocm_base  # Specific Dockerfile
```

## Description
An **intelligent comparison tool** that analyzes vllm requirements files **and Dockerfiles** between versions and provides actionable insights for AIPCC workflows. Goes beyond simple diffs to deliver impact analysis, onboarding recommendations, and concrete next steps.

**For accelerator builds** (ROCm, CUDA, CPU, TPU, XPU), Dockerfile comparison is critical because they specify exact commits/branches for dependencies built from source (PyTorch, Triton, Flash Attention, etc.) - information not available in requirements files.

**Note:** Each variant compares only the files that actually exist in the vllm repository. For example, CUDA has `cuda.txt` but no `cuda-build.txt`, while ROCm has both `rocm.txt` and `rocm-build.txt`.

**This command is valuable because it provides AI-powered analysis**, not just raw diffs:
- ✅ Identifies new packages requiring onboarding with complexity assessment
- ✅ Highlights breaking changes and version compatibility issues  
- ✅ Extracts purpose and context from requirement file comments
- ✅ **Analyzes Dockerfile ARG changes** (base images, build commits)
- ✅ Generates prioritized action items for package onboarding
- ✅ Assesses overall upgrade impact (low/medium/high)

**Comparison Modes:**
- **Variant mode**: Use short names like `rocm`, `cuda` to automatically compare runtime + build requirements **+ Dockerfiles**
  - Example: `rocm` compares `common.txt`, `rocm.txt`, `rocm-build.txt`, and Dockerfiles
- **File mode**: Specify exact filenames like `rocm-build.txt` or `docker/Dockerfile.rocm` to compare individual files
- **Output format**: Use `--pretty` flag (default) for clean summary output or `--no-pretty` for unified diff

**Use cases:**
- **Package onboarding**: Identify and prioritize new dependencies for wheels builder
- **Impact assessment**: Understand complexity before upgrading vllm versions
- **Build debugging**: Correlate requirement changes with build failures
- **Release planning**: Estimate effort and timeline for vllm upgrades
- **Variant analysis**: Track hardware-specific requirement divergence (ROCm, CUDA, etc.)

## Implementation

The command fetches requirements files directly from the vllm GitHub repository, displays the changes, and provides intelligent impact analysis for AIPCC workflows.

### AI Analysis Requirements

After displaying the comparison output, **you must analyze the changes and provide**:

1. **Impact Assessment**: Categorize as low/medium/high impact based on:
   - Number of new packages requiring onboarding
   - Major vs minor version changes
   - Removed dependencies
   - Infrastructure changes (URLs, build tools)
   - **Dockerfile ARG changes** (base images, source build commits for PyTorch/Triton/etc.)

2. **Actionable Sections**:
   - ✅ **No Action Required**: List unchanged critical dependencies
   - ⚠️ **Action Required**: New packages to onboard, investigate, or update
   - 🚨 **Breaking Changes**: Major version bumps or removed packages

3. **Package Onboarding Impact**: For each new package:
   - Purpose (from comments in requirements file)
   - Likely complexity (pure Python vs compiled)
   - PyPI link for investigation
   - Any ambiguity (e.g., multiple packages with same name)

4. **Dockerfile Analysis** (for ROCm/CUDA/CPU/TPU/XPU variants):
   - **Base image changes**: ROCm/CUDA version upgrades or downgrades
   - **Source build commits**: PyTorch, Triton, TorchVision commit changes
   - **New dependencies**: New ARGs for communication libs (UCX, MORI), frameworks, etc.
   - **Infrastructure impact**: What these changes mean for build reproducibility

5. **Next Steps**: Concrete action items for the user

6. **Context**: Infer the purpose of the update if possible (e.g., "adds support for X feature")

### Comparison Modes:

**Input Modes:**
1. **Variant mode**: Use short names (`rocm`, `cuda`, `cpu`, `tpu`, `xpu`)
   - Automatically compares runtime + build requirements + Dockerfiles for that variant
   - Each variant compares only the files that actually exist in vllm
   - Example: `rocm` → `common.txt`, `rocm.txt`, `rocm-build.txt`, `Dockerfile.rocm`, `Dockerfile.rocm_base`
   - Example: `cuda` → `common.txt`, `cuda.txt`, `Dockerfile` (no cuda-build.txt)

2. **File mode**: Specify exact filename (`rocm-build.txt`, `common.txt`, `docker/Dockerfile.rocm`, etc.)
   - Compares only that specific file
   - Useful for targeted comparisons

**Output Modes:**
1. **Regular mode**: Shows full unified diff with context lines
2. **Pretty mode** (`--pretty` flag, **RECOMMENDED**): Shows summary table + categorized changes with emojis

**Note:** Always present changes in a clean, categorized format with summary table by default (conceptually equivalent to `--pretty` mode).

### Steps:

1. **Detect input type and determine files to compare**
   
   - **Variant mode**: If input is `rocm`, `cuda`, `cpu`, `tpu`, or `xpu`:
     - Fetch the predefined file set for that variant (runtime + build + Dockerfiles)
     - Each variant has a specific configuration based on what actually exists in vllm
   - **File mode**: If input contains `.txt` or `docker/`, compare only that specific file

2. **Fetch files from GitHub**
   
   For each file to compare:
   - **Requirements files**: `https://raw.githubusercontent.com/vllm-project/vllm/{version}/requirements/{filename}`
   - **Dockerfiles**: `https://raw.githubusercontent.com/vllm-project/vllm/{version}/{dockerfile_path}`
     - Example: `https://raw.githubusercontent.com/vllm-project/vllm/v0.13.0/docker/Dockerfile.rocm`
   - Fetch both version1 and version2
   - Handle errors gracefully (file not found, version doesn't exist)

3. **Analyze and present changes**
   
   For each file:
   - Show file header (if comparing multiple files)
   - **For requirements files (.txt):**
     - **Package version changes**: Extract package name and versions (old → new)
     - **New packages**: Packages only in version2
     - **Removed packages**: Packages only in version1
     - **URL/infrastructure changes**: PyPI index URLs, etc.
   - **For Dockerfiles:**
     - **ARG changes**: Extract ARG name and value (e.g., `BASE_IMAGE=rocm/dev-ubuntu-22.04:7.1`)
     - Compare ARG values between versions (old → new)
     - Show new ARGs added and old ARGs removed
   - Present in clean format with context from comments

4. **Provide intelligent impact analysis**
   
   This is the critical value-add - transform raw changes into actionable insights!

### Requirements Files Structure:

The vllm repository organizes requirements into multiple files. **Note:** Not all variants have both runtime and build files.

**Variant configurations:**

- **ROCm**: `common.txt`, `rocm.txt`, `rocm-build.txt` + Dockerfiles (most complete)
- **CUDA**: `common.txt`, `cuda.txt` + Dockerfile (no cuda-build.txt)
- **CPU**: `common.txt`, `cpu.txt`, `cpu-build.txt` + Dockerfile.cpu
- **TPU**: `common.txt`, `tpu.txt` + Dockerfile.tpu (no tpu-build.txt)
- **XPU** (Intel GPU): `common.txt`, `xpu.txt` + Dockerfile.xpu (no xpu-build.txt)

**Dockerfiles** specify exact commits/branches for source builds (PyTorch, Triton, etc.):
- `docker/Dockerfile.rocm` and `docker/Dockerfile.rocm_base` - ROCm builds
- `docker/Dockerfile` - CUDA builds
- `docker/Dockerfile.cpu` - CPU builds
- `docker/Dockerfile.tpu` - TPU builds
- `docker/Dockerfile.xpu` - Intel XPU builds

## Examples

### Compare ROCm variant (build requirements + common)
```bash
/vllm-compare-reqs v0.10.0 v0.13.0 rocm
```

**Expected workflow and output:**

When comparing vllm v0.12.0 → v0.13.0 with `rocm` variant, the AI should:

1. **Present the changes in a clean format:**

```markdown
## Comparing vllm requirements: v0.12.0 → v0.13.0 (rocm variant - build)

### common.txt
**Changes:**
- ➕ `ijson` (NEW) - Required for mistral streaming tool parser
- ➕ `mcp` (NEW) - No comment provided

### rocm-build.txt
**Changes:**
- No changes detected
```

2. **Then provide intelligent impact analysis:**

```markdown
## Summary of Changes: vllm v0.12.0 → v0.13.0

### ROCm Build Requirements (rocm-build.txt)
**No changes detected** - The ROCm-specific build requirements remain identical.

### Common Requirements (common.txt)
**Two new dependencies added:**

1. **`ijson`** (NEW)
   - Purpose: Required for mistral streaming tool parser
   - Version: Not constrained
   - Impact: New package needs to be onboarded

2. **`mcp`** (NEW)
   - Purpose: Not specified in comments
   - Version: Not constrained
   - Impact: New package needs to be onboarded

### AIPCC Wheels Builder Impact:

**Overall Impact Level:** Low-to-Medium

#### ✅ No Action Required:
- **ROCm dependencies**: No changes to torch, triton, amdsmi
- **PyTorch ecosystem**: Remains unchanged
- **Build tools**: No updates to cmake, packaging, setuptools

#### ⚠️ Action Required:
**New packages to onboard:**

1. **`ijson`** - JSON streaming parser
   - Likely a pure Python package (easy to onboard)
   - Check PyPI: https://pypi.org/project/ijson/
   
2. **`mcp`** - Model Context Protocol or similar
   - Need to identify the correct package (multiple "mcp" packages exist)
   - Investigate vllm source code to determine correct package
   - Check if it's: `mcp` (Model Context Protocol)

#### Next Steps:
1. Identify the correct `mcp` package from vllm's context
2. Onboard `ijson` to the wheels builder
3. Onboard the correct `mcp` package
4. Test vllm 0.13.0 build with new dependencies

**Context:** This appears to be a feature release adding streaming tool parsing support for Mistral models.
```

### Compare ROCm variant (runtime + build + Dockerfiles)
```bash
/vllm-compare-reqs v0.13.0 v0.14.0rc1 rocm
```

**Expected to fetch and compare 5 files:**
1. `common.txt` (runtime)
2. `rocm.txt` (runtime ROCm-specific)
3. `rocm-build.txt` (build ROCm-specific)
4. `docker/Dockerfile.rocm`
5. `docker/Dockerfile.rocm_base`

**Example Dockerfile comparison output:**

```markdown
### docker/Dockerfile.rocm_base
**🐳 Dockerfile ARG Changes:**

**Changed:**
- `BASE_IMAGE`: `rocm/dev-ubuntu-22.04:7.1-complete` → `rocm/dev-ubuntu-22.04:7.0-complete`
- `PYTORCH_BRANCH`: `1c57644d` → `89075173`
- `PYTORCH_VISION_BRANCH`: `v0.23.0` → `v0.24.1`
- `AITER_BRANCH`: `59bd8ff2` → `6af8b687`

**Added:**
- `MORI_BRANCH=2d02c6a9`
- `MORI_REPO=https://github.com/ROCm/mori.git`
- `UCX_BRANCH=da3fac2a`
- `UCX_REPO=https://github.com/ROCm/ucx.git`

**Impact:** Base image downgraded to ROCm 7.0, PyTorch and TorchVision source commits updated, new communication libraries (MORI, UCX) added for distributed training.
```

### Compare CUDA variant
```bash
/vllm-compare-reqs v0.11.0 v0.13.0 cuda
```

### Compare specific requirements file only
```bash
/vllm-compare-reqs v0.12.0 v0.13.0 common.txt
```

### Compare specific Dockerfile
```bash
/vllm-compare-reqs v0.13.0 v0.14.0rc1 docker/Dockerfile.rocm_base
```

### Compare with raw diff output
```bash
/vllm-compare-reqs v0.13.0 v0.14.0rc1 rocm --no-pretty
```

**Expected output:**
```
Fetching rocm-build.txt for v0.10.0...
Fetching rocm-build.txt for v0.13.0...

=== Comparing rocm-build.txt: v0.10.0 -> v0.13.0 ===

Package Changes:

📦 Changed:
  torch==2.7.0 → torch==2.9.0
  torchvision==0.22.0 → torchvision==0.24.0
  torchaudio==2.7.0 → torchaudio==2.9.0
  triton==3.2 → triton==3.5.0
  amdsmi==6.2.4 → amdsmi==6.4.3

➕ Added:
  --extra-index-url https://download.pytorch.org/whl/rocm6.4
  timm>=1.0.17

URLs compared:
  https://raw.githubusercontent.com/vllm-project/vllm/v0.10.0/requirements/rocm-build.txt
  https://raw.githubusercontent.com/vllm-project/vllm/v0.13.0/requirements/rocm-build.txt
```

## Return Value

The command displays two parts:

### Part 1: Raw Comparison Data
1. **Status messages** - Fetching progress for each version
2. **Comparison output** - Depending on mode:
   - Regular mode: Unified diff with context
   - Pretty mode: Categorized changes (📦 Changed, ➕ Added, ➖ Removed)
3. **URLs** - The GitHub URLs that were compared for verification

### Part 2: AI Impact Analysis (Required)

After showing the raw data, **you must provide intelligent analysis**:

```
## Summary of Changes: vllm {version1} → {version2}

### [File Name] Requirements

**Key Changes:**
- List major changes with context

### AIPCC Wheels Builder Impact:

**Overall Impact Level:** [Low/Medium/High]

#### ✅ No Action Required:
- Critical dependencies that remain stable
- Example: PyTorch ecosystem unchanged

#### ⚠️ Action Required:
**New packages to onboard:**
1. **`package-name`** - Purpose from requirements file
   - Complexity assessment (pure Python vs compiled)
   - PyPI link: https://pypi.org/project/package-name/
   - Any concerns or ambiguities

**Version updates requiring verification:**
- List packages with major version bumps

**Removed dependencies:**
- List removed packages with impact assessment

#### 🚨 Breaking Changes:
- Major version changes
- Removed packages still in use
- Infrastructure changes (URLs, build configuration)

#### Next Steps:
1. Concrete action item 1
2. Concrete action item 2
3. ...

**Context:** [Infer the purpose of this update if possible]
```

### Interpreting the Output and Providing Analysis

**Your role is to transform raw diff data into actionable insights.** Don't just show the diff - analyze its impact!

**Example: Package version changes**
```diff
-torch==2.7.0
+torch==2.9.0
```
**Your analysis should include:**
- Version change type (major/minor/patch)
- Impact level (breaking vs safe)
- Whether torch 2.9.0 is already onboarded
- Downstream dependencies affected

**Example: New dependencies**
```diff
+timm>=1.0.17
```
**Your analysis should include:**
- Purpose (check requirement file comments)
- Whether it's pure Python or compiled (affects onboarding complexity)
- PyPI link for user to investigate
- Urgency (required for build vs optional feature)

**Example: Removed dependencies**
```diff
-scipy # Required for phi-4-multimodal-instruct
```
**Your analysis should include:**
- What functionality is affected (from comment)
- Whether this breaks existing builds
- Alternative package or workaround
- Risk assessment

**Example: URL changes**
```diff
---extra-index-url https://download.pytorch.org/whl/rocm6.2.4
+--extra-index-url https://download.pytorch.org/whl/rocm6.4
```
**Your analysis should include:**
- Infrastructure impact (ROCm version upgrade)
- Which build configuration files need updates
- Compatibility with existing packages
- Migration complexity

## Error Handling

The command handles common errors:

- **Version not found**: If a version tag doesn't exist on GitHub
  ```
  Error: Could not fetch https://raw.githubusercontent.com/vllm-project/vllm/v0.99.0/requirements/rocm-build.txt
  Version v0.99.0 may not exist in the vllm repository
  ```

- **File not found**: If the requirements file doesn't exist in that version
  ```
  Error: rocm-build.txt not found in v0.10.0
  This file may not exist in older versions
  ```

- **Network issues**: If GitHub is unreachable
  ```
  Error: Unable to connect to GitHub
  Check your network connection
  ```

## Arguments

- **version1** (required): First version to compare (older version)
  - Format: `v0.13.0`, `0.13.0`, or git commit SHA
- **version2** (required): Second version to compare (newer version)
  - Format: `v0.13.0`, `0.13.0`, or git commit SHA
- **variant|requirements-file** (required): Hardware variant or specific requirements file
  - **Variants**: `rocm`, `cuda`, `cpu`, `tpu`, `xpu` (compares runtime + build + Dockerfiles)
  - **Specific files**: `rocm-build.txt`, `common.txt`, `docker/Dockerfile.rocm`, etc. (compares single file)
- **--pretty** (optional, default enabled): Enable clean summary output
  - Shows summary table + categorized changes
  - Uses emoji indicators (📦 Changed, ➕ Added, ➖ Removed) for better readability
  - Ideal for quick overview of changes
- **--no-pretty** (optional): Show raw unified diff instead

## AIPCC Workflow Integration

This command integrates with the AIPCC wheels builder workflow by providing **actionable intelligence**, not just raw data.

### Package Onboarding
When onboarding a new vllm version to the wheels builder:
1. **Compare** requirements between current and new vllm version
2. **Analyze** each new dependency:
   - Extract purpose from requirement file comments
   - Assess onboarding complexity (pure Python vs compiled extensions)
   - Check for package ambiguity (multiple packages with same name)
   - Provide PyPI links for investigation
3. **Prioritize** changes by impact level
4. **Generate** concrete action items for the user

**AI must answer these questions:**
- What new packages need onboarding?
- What's the complexity of each (easy/medium/hard)?
- Are there any breaking changes?
- What's the recommended onboarding order?

### Debugging Build Failures
When vllm builds fail:
1. **Compare** requirements files to identify what changed
2. **Correlate** changes with build errors
3. **Identify** missing dependencies or version mismatches
4. **Recommend** fixes with specific package versions

**AI must answer these questions:**
- What changed between working and failing versions?
- Which change likely caused the failure?
- What specific package versions are required?
- Are there known compatibility issues?

### Release Planning
When planning AIPCC releases:
1. **Compare** requirements across multiple vllm versions
2. **Assess** upgrade path complexity
3. **Estimate** onboarding effort for new dependencies
4. **Identify** potential blockers (missing packages, breaking changes)
5. **Generate** release planning checklist

**AI must answer these questions:**
- How many new packages need onboarding?
- What's the estimated effort?
- Are there any high-risk changes?
- What's the recommended timeline?

### Critical Success Factor

**The value of this command is NOT the diff output** - users can see diffs on GitHub. **The value is the AI's analysis and recommendations** tailored to AIPCC workflows. Always provide context, impact assessment, and actionable next steps.

## See Also
- **vllm GitHub Repository**: https://github.com/vllm-project/vllm
- **AIPCC Package Onboarding Guide**: Internal documentation for onboarding new packages
- **Fromager Documentation**: https://fromager.readthedocs.io/

