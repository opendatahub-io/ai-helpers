---
name: env-finder
description: Investigate environment variables that can be set when building Python wheels for a given project. Analyzes setup.py, CMake files, and other build configuration files to discover customizable build environment variables.
allowed-tools: [Bash, Read, Grep, Glob]
---

# Python Build Environment Variables Investigation

This skill helps you discover all environment variables that can be set when building Python wheels for a project. It performs a comprehensive analysis of build configuration files to identify customizable environment variables used during the wheel building process.

## Instructions

When a user asks about environment variables for building Python wheels, investigating build configuration, or understanding build customization options:

1. **Run the Environment Variables Investigation Script**:
   ```bash
   ./scripts/env_finder.py [project_path]
   ```

2. **Analyze and present the findings** focusing on:

   ### Build Configuration Variables
   - **Setup.py Variables**: Environment variables used in setup.py for customizing builds
   - **CMake Variables**: Variables defined in CMakeLists.txt and related files
   - **Build Tool Variables**: Variables used by setuptools, distutils, or other build systems
   - **Compiler Variables**: Variables affecting compilation (CC, CXX, CFLAGS, etc.)

   ### Variable Categories

   #### Compiler and Linker Variables
   - `CC`, `CXX` - Compiler selection
   - `CFLAGS`, `CXXFLAGS` - Compilation flags
   - `LDFLAGS` - Linker flags
   - `LIBS` - Additional libraries

   #### Path Configuration Variables
   - `PREFIX` - Installation prefix
   - `LIBRARY_PATH` - Library search paths
   - `INCLUDE_PATH` - Header file paths
   - `PKG_CONFIG_PATH` - pkg-config search paths

   #### Feature Control Variables
   - `ENABLE_*` - Feature enable/disable flags
   - `WITH_*` - Optional component inclusion
   - `USE_*` - Build option selection
   - `DISABLE_*` - Feature disable flags

   #### Python-Specific Variables
   - `PYTHON_INCLUDE_DIR` - Python headers location
   - `PYTHON_LIBRARY` - Python library path
   - `SETUPTOOLS_*` - Setuptools configuration
   - `PIP_*` - pip-related build variables

   ### Usage Context
   - **When Variables Are Used**: During which build phase each variable takes effect
   - **Default Values**: What happens when variables are not set
   - **Required vs Optional**: Which variables are mandatory for successful builds

3. **Provide actionable guidance**:
   - How to set each variable for custom builds
   - Common use cases for each variable
   - Potential conflicts or compatibility issues
   - Recommended values for different scenarios

## Output Format

The skill should provide a structured list of environment variables with:

1. **Variable Name**: Exact environment variable name
2. **Purpose**: Clear description of what the variable controls
3. **Type**: Expected value type (path, boolean, string, number)
4. **Default Value**: What happens when not set
5. **Source File**: Where the variable was discovered
6. **Usage Context**: When and how the variable is used

## Error Handling and Edge Cases

### No Build Configuration Found
- Report that no environment variables were found
- Most packages don't have build configuration so it is fine

