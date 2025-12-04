---
description: Analyze RPM build.log failures
argument-hint: [copr-chroot-url] OR [build-log-url] [srpm-url] OR [build.log] [specfile|dist-git] [sources]
---

## Name
rpm:examine

## Synopsis
```
/rpm:examine <copr-chroot-url>
/rpm:examine <build-log-url> <srpm-url>
/rpm:examine <build.log> <specfile|dist-git> [sources]
```

## Description
Analyze RPM build.log failures. Provide a comprehensive analysis with error summary, root cause, and actionable fixes.

### Mode 1: Copr Results URL or Direct URLs to build.log and SRPM
Provide a single Copr build results URL to automatically fetch all build artifacts or provide two URLs - one for build.log and one for SRPM.

**What gets downloaded:**
- `build-live.log.gz` or `build.log` - Main build log
- `*.src.rpm` - Source RPM containing spec file, sources, and patches
- `root.log.gz`, `state.log` - Additional context logs (optional)

### Mode 2: Local Files
Provide paths to local build artifacts.

**Arguments:**
1. `<build.log>` - Path to build log file (required)
2. `<specfile|dist-git>` - Path to spec file or dist-git repo clone (required)
3. `[sources]` - Path to source tarball or unpacked sources (optional)

**Context gathering:**
If sources not provided, search in:
- build.log parent directory
- specfile parent directory
- dist-git clone directory

## Implementation

### 1. Input Detection
- **If single URL**: Copr results directory → continue to step 2a
- **If two URLs**: Direct URLs to build.log and SRPM (Koji/Brew) → download both directly, then follow 2a steps 3-5
- **If local path(s)**: Local workflow → continue to step 2b

### 2. Artifact Collection

#### 2a. URL Workflow
1. Create temporary working directory
2. Download files from Copr URL:
   ```bash
   curl -LO <copr-url>/builder-live.log.gz
   curl -LO <copr-url>/*.src.rpm
   curl -LO <copr-url>/root.log.gz      # optional
   curl -LO <copr-url>/state.log        # optional
   ```
3. Decompress logs: `gunzip *.log.gz` (if needed)
4. Extract SRPM: `rpm2cpio *.src.rpm | cpio -idmv`
5. Locate extracted spec file

#### 2b. Local Workflow
1. Verify build.log exists and is readable
2. Verify specfile/dist-git path exists
3. Search for sources if not provided:
   - Check build.log parent directory for `*.tar.*` or `*.src.rpm`
   - Check specfile parent directory
   - If dist-git repo, check for sources in repo

### 3. Context Gathering
Collect all relevant information before analysis:

**Spec file analysis:**
- BuildRequires dependencies
- Patches and their application order
- Macros and their expansions
- Build steps (%prep, %build, %install, %check, %files)

**Additional context:**
- For dist-git repos: Run `git diff` to check uncommitted changes
- Examine patch files for conflicts or application failures
- Look for auxiliary files: `%{name}.conf`, `%{name}.desktop`, systemd units
- Check for additional logs: `root.log`, `state.log`, `mock.log`

**Source code (if needed):**
- For compiler errors: Unpack sources to examine code
- For test failures: Locate test files and configurations
- For build system issues: Check `CMakeLists.txt`, `Makefile.am`, `setup.py`, etc.

### 4. Analysis

#### Scan Strategy
1. **Start at the end**: Scan build.log from bottom up to find failure point
2. **Identify the phase**: Determine which RPM build phase failed:
   - `%prep` - Source unpacking and patch application
   - `%build` - Compilation and building
   - `%install` - Installation to buildroot
   - `%check` - Test suite execution
   - Binary RPM creation - File packaging
3. **Find the trigger**: Locate exact command or operation that failed
4. **Trace backwards**: Follow the chain of events leading to failure
5. **Cross-reference**: Compare findings with specfile configuration

#### Error Keywords to Search
- `"Error:"`, `"FAILED"`, `"fatal error:"`
- `"configure: error:"`, `"No such file"`
- `"undefined reference"`, `"make: ***"`
- `"CMake Error"`, `"ninja: build stopped"`
- `"ModuleNotFoundError"`, `"ImportError"`
- `"Ignoring extra path from command line"` - May indicate broken line continuation in spec file
- `"add_subdirectory given source"` + `"not an existing directory"` - May indicate missing options due to spec formatting

#### Hard To Find Error Patterns

**Spec file whitespace issues:**
- Trailing space after backslash (`\ ` instead of `\`) - Breaks line continuation, causing subsequent lines to be completely ignored by the shell
- Missing backslash in multi-line constructs (especially in `%if` blocks)
- **Detection**: Use `cat -A specfile.spec` to reveal trailing spaces (shows as `\ $` at end of line) or `grep '\\ $' specfile.spec`
- **Symptoms**: CMake/configure options appear ignored, features default to wrong values, mysterious "directory not found" errors

### 5. Cleanup
- If URL workflow was used, clean up temporary directory after analysis
- Ask user before cleanup if they might need files for further investigation

## Output Format

Provide a clear, structured analysis:

### 1. Error Summary
Brief description of what failed (1-2 sentences)

### 2. Root Cause
Technical explanation of why it failed:
- Which phase encountered the error
- What operation or command triggered it
- Underlying technical reason

### 3. Suggested Fixes
Specific, actionable steps to resolve:
- Exact changes needed (with code/spec snippets if applicable)
- Commands to run
- Dependencies to add/modify
- Patches to apply/modify

### 4. Additional Recommendations
Optional section for:
- Related improvements
- Potential future issues
- Best practices
- Warnings about side effects
