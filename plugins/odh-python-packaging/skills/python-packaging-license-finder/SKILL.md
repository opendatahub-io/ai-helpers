---
name: python-packaging-license-finder
description: Use this skill to deterministically find license information for Python packages by checking PyPI metadata first, then falling back to Git repository LICENSE files using shallow cloning.
allowed-tools: Bash Skill
---

# Python Package License Finder

This skill helps you deterministically find license information for Python packages using a two-step approach: first checking PyPI metadata, then searching the source repository if needed.

## Instructions

When a user asks to find the license for a Python package, follow this deterministic process:

### Step 0: Source URL Priority

If a source repository URL is provided by the caller, skip PyPI lookup entirely:

1. Pass the URL directly to the `git:shallow-clone` skill
2. Search for LICENSE files in the cloned repository (see Step 2.3-2.4 below)
3. Report the license found

You can also use the script with a source URL to trigger this flow:
```bash
./scripts/find_license.py <package_name> --source-url <url>
```

If no source URL is provided, proceed with Step 1.

### Step 1: Check PyPI Metadata
First, attempt to find the license from PyPI using the package inspection script:

```bash
./scripts/find_license.py <package_name> [version]
```

If the script finds a license in the PyPI metadata, **stop here** and return the license name.

### Step 2: Search Git Repository (if PyPI fails)
If no license is found in PyPI metadata, search the package's source repository:

1. **Get the source repository URL** from the PyPI metadata (the script will provide it)
2. **Use the shallow-clone skill** to clone the repository:
   ```
   Skill: git:shallow-clone
   ```
3. **Search for LICENSE files** in the cloned repository:
   ```bash
   find . -iname "license*" -o -iname "copying*" -o -iname "copyright*" | head -10
   ```
4. **Read the license file** to identify the license type:
   ```bash
   head -20 <license_file>
   ```

### Step 3: Report Results
- **License Found**: Return the license name (e.g., "MIT License", "Apache-2.0", "GPL-3.0")
- **License Not Found**: Report that the license could not be determined

## Usage Examples

### Find License for Popular Package
```bash
./scripts/find_license.py requests
```
**Expected**: Find "Apache-2.0" from PyPI metadata

### Find License for Package with Missing PyPI License
```bash
./scripts/find_license.py some-package
```
**Expected**: Fall back to repository search if PyPI metadata is incomplete

### Specific Version Analysis
```bash
./scripts/find_license.py django 4.2.0
```
**Expected**: Find license for specific Django version

## Error Handling

### Package Not Found
- Verify package name spelling
- Check package availability on PyPI
- Suggest alternative package names

### Repository Access Issues
- Report if source repository is unavailable
- Note private/restricted repositories
- Suggest manual license verification

### License File Parsing
- Handle non-standard license file formats
- Report unclear or multiple licenses
- Recommend manual review for complex cases

## Integration Notes

This skill complements:
- **python-packaging-complexity** - License info helps assess redistribution complexity
- **python-packaging-license-checker** - Provides license names for compatibility assessment
- **python-packaging-source-finder** - Uses similar PyPI metadata analysis

The skill focuses on **finding** license information, while license-checker focuses on **assessing** license compatibility for redistribution.
