---
name: python-packaging-git-audit
description: Inspect recent git history of a Python package repository for suspicious commits touching supply-chain-sensitive files, then triage findings with AI reasoning to produce a structured risk report section.
allowed-tools: Bash Read Grep
---

# Python Packaging Git Audit

Inspects the recent git history of a Python package repository for commits
that modify supply-chain-sensitive files (setup.py, CI configs, .pth files,
etc.) and contain suspicious patterns. Produces a self-contained "Git History
Analysis" report section with triaged findings and a risk assessment.

## Inputs

- **repo_path** (required): Local filesystem path to a git repository
- **output_file** (optional): Write the report section to this file path instead of
  returning it inline. The first line of the file must be `RISK_RATING:<value>` so
  the orchestrator can parse it without reading the full report.

## Step 1: Enumerate Commits

Determine the number of commits available and scan up to the last 50:

```bash
git -C <repo-path> log -50 --format='%H'
```

## Step 2: Filter Sensitive Files

From those commits, identify ones that modify supply-chain-sensitive files:

- `setup.py`, `setup.cfg`, `pyproject.toml`, `MANIFEST.in`
- `.github/workflows/*.yml`, `.gitlab-ci.yml`
- Any `.pth` files
- `__init__.py` files at package root

```bash
git -C <repo-path> log -50 --diff-filter=ACMR --name-only --format='COMMIT:%H|%aI|%ae' -- \
  setup.py setup.cfg pyproject.toml MANIFEST.in \
  '.github/workflows/*.yml' .gitlab-ci.yml \
  '*.pth' '*/__init__.py'
```

## Step 3: Search for Suspicious Patterns

For each flagged commit, extract the diff and search for suspicious patterns:

- **Code execution**: `eval(`, `exec(`, `compile(`
- **Process spawning**: `subprocess`, `os.system`, `os.popen`
- **Encoding/serialization**: `base64`, `marshal`, `pickle`
- **Network access**: `socket`, `urllib`, `requests.get`, `httpx`
- **Native code**: `ctypes`, `cffi`
- **Embedded URLs**: `http://`, `https://`

```bash
git -C "<repo-path>" show --format= -m --first-parent "<commit>" -- "<file>" | \
  grep -nE 'eval\(|exec\(|compile\(|subprocess|os\.system|os\.popen|base64|marshal|pickle|socket|urllib|requests\.get|httpx|ctypes|cffi|https?://'
```

Collect per finding: commit hash, author, date, file modified, and matching patterns.

## Step 4: Triage

Review git history findings with AI reasoning. There are no deterministic rules
for this phase — each finding requires contextual judgment.

For each flagged commit, consider:

- Is this a normal dependency version bump or configuration change?
- Does the pattern match the package's stated purpose?
- Is the author a known maintainer with a history of contributions?
- Does the change introduce new capabilities that seem out of scope?

Flag commits that introduced suspicious patterns into sensitive files. Assign
a verdict to each:

- **Likely legitimate** — change is a normal maintenance or dependency update
- **Suspicious** — change introduces unexpected capabilities or patterns
- **Critical** — change strongly indicates malicious intent (e.g., encoded payload in install hook)

## Output Format

Produce the following markdown section:

```markdown
## Git History Analysis (Last 50 Commits)

**Commits touching sensitive files:** {N}

| Commit | Date | Author | File | Patterns Found |
|--------|------|--------|------|----------------|
| abc1234 | 2026-03-15 | user@example.com | setup.py | subprocess, os.system |

**AI Assessment:** {Brief narrative on whether the git history changes look normal or concerning, with reasoning}
```

The **risk_rating** for this phase is one of:

- **no_issues** — No sensitive files modified in recent history
- **low_risk** — All findings classified as "likely legitimate"
- **needs_review** — One or more findings classified as "suspicious"
- **critical** — One or more findings classified as "critical"

If `output_file` is provided, write the file with the first line as
`RISK_RATING:<value>` followed by a blank line and then the markdown section
above. If `output_file` is not provided, return the report section inline.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Path is not a git repository | Report "not a git repository", risk_rating = needs_review |
| Fewer than 50 commits available | Scan all available commits, note count in report |
| No sensitive files modified in history | Report "no sensitive files found", risk_rating = no_issues |
