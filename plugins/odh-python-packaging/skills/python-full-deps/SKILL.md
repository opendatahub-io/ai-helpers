---
name: python-full-deps
description: Resolve the full install-time dependency tree for a Python package. Use when the user needs all transitive dependencies, full dependency list, or install requirements resolved for a specific Python version with environment markers.
allowed-tools: Bash Read
compatibility: Requires network access to PyPI. Requires uv (preferred) or pip >= 22.2 (fallback).
---

# Python Full Dependency Tree

Resolve and return the complete set of packages that would be installed for a given Python package (entire transitive dependency tree), resolved for a specific Python version so environment markers are respected.

## When to use

- User asks for "full dependency tree", "all dependencies", "transitive dependencies", or "install requirements" of a Python package.
- User needs the full picture of install-time dependencies (not just direct deps from metadata).
- User wants to understand the total footprint of a package in a container image or environment.
- Complement to `python-packaging-complexity` when the full resolved tree is needed beyond direct metadata.

## When NOT to use

- User only needs **direct** (first-level) dependencies -- use `python-packaging-complexity` instead, which reads PyPI metadata without resolution.
- User is asking about **build-time** dependencies (e.g. setuptools, CMake, Cython) -- those are not included in install-time resolution.
- User is asking about **dev/test** dependencies (e.g. pytest, mypy) -- those are extras, not default install deps.
- User is asking about **license**, **source**, or **build complexity** analysis -- use the corresponding `python-packaging-*` skills.

## Inputs

| Parameter       | Required | Default | Description                         |
|-----------------|----------|---------|-------------------------------------|
| package name    | Yes      | —       | PyPI project name (e.g. `vllm`)     |
| package version | No       | latest  | e.g. `0.4.0`                        |
| Python version  | No       | 3.12    | e.g. `3.11`, `3.12`                 |

## Instructions

When a user asks about the full dependency tree, all transitive dependencies, or install requirements for a Python package:

1. **Run the helper script** with the package name and optional version/Python version:

   ```bash
   python3 scripts/resolve_full_deps.py <package> [version] [python_version]
   ```

   The script automatically tries `uv pip compile` first (fast, supports cross-version resolution). If `uv` is not installed, it falls back to `pip install --dry-run --report` in a temporary venv.

2. **Present the output** to the user:
   - Output is sorted alphabetically and deduplicated.
   - Each line is `name==version` with PEP 503 normalized names.
   - Warnings/errors go to stderr and should be relayed to the user.

3. **Provide context** based on the results:
   - Total number of transitive dependencies.
   - Notable packages in the tree (e.g. `torch`, `numpy`, `cuda` related packages).
   - If the user is assessing container image size or supply-chain risk, highlight the dependency count and any heavy packages.

## Output format

Return a **sorted, unique** set of normalized dependencies. Include version unless the user asked for names only.

- One dependency per line: `name==version`
- Or as a list: `["package-a==1.0.0", "package-b==2.1.0"]`

### Example

```bash
$ python3 scripts/resolve_full_deps.py requests 2.32.3
certifi==2024.8.30
charset-normalizer==3.4.1
idna==3.10
requests==2.32.3
urllib3==2.3.0
```

Interpretation: `requests 2.32.3` pulls in 4 transitive dependencies (5 total including itself).

## Error handling

- **`uv` not found**: The script automatically falls back to pip. If the user sees a stderr warning about this, suggest installing [uv](https://docs.astral.sh/uv/) for faster resolution.
- **Package not found on PyPI**: The script exits with a non-zero code and an error on stderr. Verify the package name spelling and whether a specific version exists.
- **Network errors / timeouts**: Both `uv` and `pip` need network access to PyPI. If resolution times out (150s), suggest retrying or checking network connectivity.
- **pip version too old**: The `--report` flag requires pip >= 22.2. If the fallback fails with an unrecognized argument error, advise upgrading pip.

## Integration with other skills

- **`python-packaging-complexity`**: Use that skill first to get direct dependencies and build complexity, then use this skill to get the full transitive tree. Together they give a complete picture.
- **`python-packaging-license-checker`** / **`python-packaging-license-finder`**: After getting the full dep list from this skill, feed individual packages into the license skills to audit the entire tree.
