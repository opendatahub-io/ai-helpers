---
name: python-packaging-bug-finder
description: "Find known packaging bugs, fixes, and workarounds for Python projects by searching GitHub issues and analyzing their resolution status. Use when the user encounters pip install errors, dependency conflicts, build failures, or wants to check if a packaging problem is a known issue with available fixes or workarounds."
allowed-tools: Skill WebFetch WebSearch
---

# Python Packaging Bug Finder

Identifies known packaging and build issues for Python projects by searching their GitHub repositories for relevant issues and determining resolution status.

## Instructions

### 1. Find the Repository

Use the source finder skill to locate the project's GitHub repository:

```
Skill: python-packaging-source-finder
Args: <package_name>
```

If confidence is low or no URL found, report the error and stop.

### 2. Search for Packaging Issues

Once you have the repository URL:

1. Use WebFetch to access `<repo_url>/issues` and filter for packaging keywords: `build`, `install`, `pip`, `wheel`, `setup.py`, `pyproject.toml`, `cmake`, `compile`, `dependency`, `version conflict`
2. Prioritize open issues first, then closed ones that might affect the target version

### 3. Analyze Each Relevant Issue

For each packaging-related issue, use WebFetch to get the full issue page and extract:

- **Problem**: What packaging/build problem is described
- **Affected versions**: Which versions are mentioned as problematic
- **Resolution status**: Fixed (with version), pending, workaround available, or unresolved
- **Available fixes**: PRs, commits, or workarounds mentioned in comments

Look for resolution indicators: "fixed in PR #XXX", "merged in #XXX", commit SHAs, "fixed in v1.X.X", "workaround" comments.

### 4. Version Impact Assessment

For each issue, determine whether it affects the target version and classify:

- **Fixed and Included**: Fix available in target version
- **Fixed but Pending**: Fix exists but not yet in target version
- **Open with Workarounds**: No fix but workarounds available
- **Unresolved**: Open with no clear solution

## Output Format

```markdown
# Packaging Issues Analysis for <package_name> [version]

## Repository
- URL: <repository_url>
- Confidence: <high/medium/low>

## Issues Found: X total

### [Status] Issue Title
- **URL**: <issue_url>
- **Problem**: <brief_description>
- **Affects Target Version**: Yes/No/Unknown
- **Resolution**: <type and details>
- **Workarounds**: <if available>
- **Recommendation**: <action_to_take>

## Summary
- Total packaging issues: X
- Affecting target version: X
- With available fixes: X
- With workarounds only: X
- Unresolved: X
```
