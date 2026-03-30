---
name: python-packaging-complexity
description: "Analyze Python package build complexity by inspecting PyPI metadata. Evaluates compilation requirements, dependency types, distribution availability, and wheel coverage gaps to recommend build strategies. Use when the user asks about Python package build complexity, wheel availability, compilation requirements, or whether to build from source vs use existing wheels."
allowed-tools: Bash Read
---

# Python Package Build Complexity Analysis

Evaluate the build complexity of Python packages by analyzing their PyPI metadata to determine compilation requirements, assess build difficulty, and recommend wheel building strategies.

## Instructions

### 1. Run the PyPI Inspection Script

```bash
./scripts/pypi_inspect.py <package_name> [version]
# For structured output:
./scripts/pypi_inspect.py <package_name> [version] --json
```

### 2. Analyze and Report

From the script output, provide analysis covering:

- **Compilation Requirements**: Whether the package needs C/C++/Rust/Fortran compilation, based on classifiers, keywords, and dependency signatures
- **Complexity Score**: The numerical score (0-10+ scale) and what drives it
- **Distribution Analysis**: Source distribution availability, existing wheel types (platform-specific vs universal), and gaps in wheel coverage
- **Dependency Complexity**: Dependencies that themselves require compilation and how they affect overall build difficulty

### 3. Provide Recommendations

Based on the analysis:

- Whether to build from source or use existing wheels
- Required build tools and dependencies
- Platform-specific considerations

## Error Handling

If the script fails or the package is not found, check for alternate package names and suggest alternative analysis approaches.

## Integration

This skill works well with **python-packaging-license-finder** for assessing redistribution requirements alongside build complexity.
