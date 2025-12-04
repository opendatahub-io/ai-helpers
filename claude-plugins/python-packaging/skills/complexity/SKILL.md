---
name: complexity
description: Analyze Python package build complexity by inspecting PyPI metadata. Evaluates compilation requirements, dependencies, distribution types, and provides recommendations for wheel building strategies.
allowed-tools: [Bash, Read]
---

# Python Package Build Complexity Analysis

This skill helps you evaluate the build complexity of Python packages by analyzing their PyPI metadata. It determines whether a package likely requires compilation, assesses build complexity, and provides recommendations for wheel building strategies.

## Instructions

When a user asks about Python package build complexity, building wheels, or evaluating PyPI packages for compilation requirements:

1. **Run the PyPI inspection script** using the package name and optional version:
   ```bash
   ./scripts/pypi_inspect.py <package_name> [version]
   ```

2. **Analyze the output** and provide interpretation focusing on:

   ### Build Complexity Assessment
   - **Compilation Requirements**: Whether the package needs C/C++/Rust/Fortran compilation
   - **Complexity Score**: Numerical score indicating build difficulty (0-10+ scale)
   - **Key Indicators**: Specific classifiers, keywords, or dependencies that suggest complexity

   ### Distribution Analysis
   - **Source Distribution Availability**: Whether sdist is available for building
   - **Existing Wheels**: What wheel types already exist (platform-specific, universal)
   - **Wheel Coverage**: Gaps in wheel availability that might need custom builds

   ### Dependency Analysis
   - **Complex Dependencies**: Dependencies that themselves require compilation
   - **Version Constraints**: Python version requirements and compatibility
   - **Transitive Complexity**: How dependencies affect overall build complexity

3. **Provide actionable recommendations**:
   - Whether to build from source or use existing wheels
   - Required build tools and dependencies
   - Platform-specific considerations
   - Estimated build time and resource requirements

## Key Complexity Indicators

### High Complexity (Score 5+)
- Native extensions (C/C++/Rust/Fortran classifiers)
- CUDA/GPU acceleration keywords
- Known complex packages (torch, tensorflow, numpy, scipy)
- Missing or limited wheel availability
- Many compiled dependencies

### Medium Complexity (Score 2-4)
- Some compilation indicators in description/keywords
- Platform-specific wheels only
- Mixed dependency complexity
- Moderate build requirements

### Low Complexity (Score 0-1)
- Pure Python packages
- Universal wheels available
- Simple dependencies
- No compilation requirements

## Usage Examples

### Basic Package Analysis
```bash
./scripts/pypi_inspect.py torch
```
**Interpretation**: Analyze latest PyTorch version for build complexity, focusing on CUDA dependencies and compilation requirements.

### Specific Version Analysis
```bash
./scripts/pypi_inspect.py numpy 1.24.3
```
**Interpretation**: Evaluate specific numpy version, explaining why numpy requires compilation and what build tools are needed.

### JSON Output for Processing
```bash
./scripts/pypi_inspect.py tensorflow --json
```
**Interpretation**: Get structured data for programmatic analysis, then explain the complexity factors in plain language.

## Providing Recommendations

Based on the analysis, provide specific guidance:

### For High Complexity Packages
- "This package requires significant compilation infrastructure"
- "Consider using pre-built wheels when available"
- "Building from source will need: [specific tools]"
- "Estimated build time: [timeframe]"

### For Wheel Building Strategies
- "Universal wheels available - use those for maximum compatibility"
- "Platform-specific wheels needed for: [platforms]"
- "Source build recommended for: [specific scenarios]"
- "Dependencies that complicate building: [list]"

### For Development Planning
- "Budget [time] for build environment setup"
- "Consider containerized builds for reproducibility"
- "Test on target platforms before production deployment"
- "Monitor for new wheel releases that might eliminate build needs"

## Error Handling

If the script fails or package is not found:
- Verify package name spelling and availability on PyPI
- Check if the package exists under a different name
- Suggest alternative analysis approaches
- Provide general guidance for unknown packages

## Integration Notes

This skill works best when combined with:
- Package dependency analysis
- Build environment setup
- Continuous integration planning
- Container build strategies
