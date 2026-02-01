---
name: python-packaging-bug-finder
description: Find known packaging bugs, fixes, and workarounds for Python projects by searching GitHub issues and analyzing their resolution status
allowed-tools: Skill WebFetch WebSearch
---

# Python Packaging Bug Finder

Identifies known packaging and build issues for Python projects by searching GitHub repositories for relevant issues, analyzing their content and comments, and determining resolution status.

## Instructions

When investigating packaging problems for a Python project, follow this workflow:

### 1. Find the Repository

Use the source finder skill to locate the project's GitHub repository:

```
Skill: python-packaging-source-finder
Args: <package_name>
```

If the skill returns a repository URL with high or medium confidence, proceed. If confidence is low or no URL found, stop here and return an error.

### 2. Search for Packaging Issues

Once you have the repository URL, search for packaging-related issues by:

1. **Access the GitHub issues page**: Use WebFetch to get the repository's issues page (typically `<repo_url>/issues`)

2. **Filter for packaging keywords**: Look for issues with titles containing:
   - Build-related: "build", "compilation", "compile", "setup.py", "pyproject.toml", "cmake", "makefile"
   - Installation: "install", "pip", "wheel", "package", "packaging", "distribution"
   - Environment: "gcc", "clang", "msvc", "python", "version", "dependency"
   - Platform: "windows", "linux", "macos", "arm64", "x86_64"
   - Errors: "error", "fail", "broken", "issue"

3. **Prioritize open issues**: Focus on open issues first, then closed ones that might affect the target version

### 3. Analyze Each Relevant Issue

For each packaging-related issue found:

1. **Fetch issue details**: Use WebFetch to get the full issue page including:
   - Issue description
   - All comments
   - Labels and milestones
   - Current status (open/closed)

2. **Extract key information**:
   - **Problem description**: What packaging/build problem is described?
   - **Affected versions**: Which versions are mentioned as problematic?
   - **Resolution status**: Is it fixed, pending, or unresolved?
   - **Available fixes**: Are there PRs, commits, or workarounds mentioned?
   - **Version inclusion**: If fixed, in which version was the fix included?

3. **Look for resolution indicators**:
   - **Fixed with PR**: Comments mentioning "fixed in PR #XXX" or "merged in #XXX"
   - **Fixed with commit**: Comments with commit SHAs or "fixed in commit XXX"
   - **Version mentions**: "fixed in v1.X.X" or "available in next release"
   - **Workarounds**: Comments with "workaround", "temporary fix", "try this"
   - **Status updates**: "resolved", "closed as fixed", "duplicate of #XXX"

### 4. Version Impact Assessment

For each issue, determine:

1. **Does it affect the target version?**
   - Compare mentioned problematic versions with target version
   - Check if fix is included in target version
   - Look for version-specific comments

2. **What's the resolution status?**
   - **Fixed and Included**: Fix is available and included in target version
   - **Fixed but Pending**: Fix exists but not yet in target version
   - **Open with Workarounds**: No fix but workarounds available
   - **Unresolved**: Open issue with no clear solution

## Output Format

Provide a structured analysis:

```markdown
# Packaging Issues Analysis for <package_name> [version]

## Repository
- URL: <repository_url>
- Confidence: <high/medium/low>

## Issues Found: X total

### [Issue Status] Issue Title
- **URL**: <issue_url>
- **Status**: Open/Closed
- **Labels**: <relevant_labels>
- **Problem**: <brief_description>
- **Affects Target Version**: Yes/No/Unknown
- **Resolution**:
  - Type: Fixed/Pending/Workaround/Unresolved
  - Details: <fix_description>
  - Available in: <version_if_applicable>
- **Workarounds**: <list_of_workarounds>
- **Recommendation**: <action_to_take>

## Summary
- Total packaging issues: X
- Affecting target version: X
- With available fixes: X
- With workarounds only: X
- Unresolved: X
```

## Issue Categories to Search For

### Build System Issues
- **Keywords**: "build fails", "compilation error", "setup.py error", "pyproject.toml", "cmake error"
- **Typical problems**: Build configuration, missing dependencies, tool compatibility

### Compiler Issues
- **Keywords**: "gcc", "clang", "msvc", "compiler error", "linker error", "C++ standard"
- **Typical problems**: Compiler version compatibility, C++ standard issues, linking problems

### Platform-Specific Issues
- **Keywords**: "windows", "linux", "macos", "arm64", "x86_64", "architecture"
- **Typical problems**: Platform-specific build failures, architecture compatibility

### Dependency Issues
- **Keywords**: "dependency", "requirements", "version conflict", "missing"
- **Typical problems**: Missing build dependencies, version conflicts, circular dependencies

### Installation Issues
- **Keywords**: "pip install", "wheel", "sdist", "packaging", "distribution"
- **Typical problems**: Installation failures, wheel building issues, PyPI problems

## Analysis Guidelines

### Effective Issue Analysis
1. **Read the original description carefully** - often contains version info and problem details
2. **Scan all comments chronologically** - resolution often emerges in later comments
3. **Look for maintainer responses** - project maintainers often provide authoritative status updates
4. **Check linked PRs and commits** - follow references to understand fix implementation
5. **Note milestone assignments** - indicates planned fix version

### Common Resolution Patterns
- **"Fixed in PR #XXX"** → Check if PR is merged and in which version
- **"Workaround: use version X.Y"** → Temporary solution available
- **"Duplicate of #XXX"** → Check the referenced issue for resolution
- **"Resolved in latest"** → Fix may be in development branch
- **Milestone assignments** → Indicates planned fix version

The bug finder provides critical context for making informed decisions about package building, version selection, and issue avoidance strategies.
