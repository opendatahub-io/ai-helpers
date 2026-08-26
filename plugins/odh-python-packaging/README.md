# odh-python-packaging

Python package analysis, security auditing, and build complexity assessment

## Install

```text
/plugin marketplace add opendatahub-io/ai-helpers
/plugin install odh-python-packaging@odh-ai-helpers
```

## Skills

- **python-full-deps** — Resolve the full install-time dependency tree for a Python package.
- **python-packaging-binary-audit** — Scan a Python package repository for compiled/binary files using Fromager-style detection and malcontent YARA analysis, then triage findings with deterministic….
- **python-packaging-bug-finder** — Use when you need to find known packaging bugs, fixes, and workarounds for Python projects by searching GitHub issues and analyzing their resolution status.
- **python-packaging-complexity** — Use this skill to analyze Python package build complexity by inspecting PyPI metadata.
- **python-packaging-env-finder** — Use this skill to investigate environment variables that can be set when building Python wheels for a given project.
- **python-packaging-git-audit** — Inspect recent git history of a Python package repository for suspicious commits touching supply-chain-sensitive files, then triage findings with AI reasoning ….
- **python-packaging-license-checker** — Use this skill to check whether a Python package license is compatible with redistribution in Red Hat products, using the Fedora License Data as the authoritat….
- **python-packaging-license-finder** — Use this skill to deterministically find license information for Python packages by checking PyPI metadata first, then falling back to Git repository LICENSE f….
- **python-packaging-security-audit** — Use this skill to evaluate the security of a Python package repository by orchestrating static analysis, binary scanning, and git history inspection sub-skills….
- **python-packaging-source-finder** — Use this skill to locate source code repositories for Python packages by analyzing PyPI metadata, project URLs, and code hosting platforms like GitHub, GitLab,….
- **python-packaging-static-audit** — Run hexora static analysis on a Python package repository to detect suspicious code patterns, then triage findings with deterministic rules and AI reasoning to….

## Agents

- **python-packaging-investigator** — Investigates Python package repositories to analyze build systems, dependencies, and packaging complexity.
