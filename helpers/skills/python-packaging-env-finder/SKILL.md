---
name: python-packaging-env-finder
description: "Investigate environment variables that can be set when building Python wheels for a given project. Analyzes setup.py, CMake files, and other build configuration files to discover customizable build environment variables. Use when the user asks about configurable environment variables for building Python packages, compiling wheels, or customizing build options in setup.py or CMakeLists.txt."
allowed-tools: Bash Read Grep Glob
---

# Python Build Environment Variables Investigation

Discover all environment variables that can be set when building Python wheels for a project by analyzing build configuration files.

## Instructions

### 1. Run the Investigation Script

```bash
./scripts/env_finder.py [project_path]
```

### 2. Analyze and Present Findings

From the script output, organize discovered variables by category:

- **Compiler/Linker**: Variables affecting compilation (e.g., `CC`, `CXX`, `CFLAGS`, `LDFLAGS`)
- **Path Configuration**: Library and header search paths
- **Feature Control**: `ENABLE_*`, `WITH_*`, `USE_*`, `DISABLE_*` flags controlling optional components
- **Python-Specific**: Python headers, library paths, setuptools/pip configuration

For each variable, report:
1. **Name**: Exact environment variable
2. **Purpose**: What it controls
3. **Default**: Behavior when not set
4. **Source File**: Where it was discovered

### 3. Provide Guidance

- How to set each variable for custom builds
- Common use cases and recommended values
- Potential conflicts or compatibility issues

## Edge Cases

If no build configuration is found, report that no environment variables were discovered. Most pure Python packages have no build configuration, which is expected.
