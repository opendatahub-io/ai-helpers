---
name: python-packaging-security-audit
description: Use this skill to evaluate the security of a Python package repository with static code analysis and a scan of git history for suspicious commits, then triaging findings to produce an actionable security report with a risk rating.
allowed-tools: Bash Read Grep Skill
---

# Python Packaging Security Audit

Designed for pre-onboarding evaluation of Python packages. Combines automated static analysis (hexora) with git history inspection to surface supply-chain risks before a package enters the build pipeline.

## Inputs

- **repo_path** (optional): Local filesystem path to an already-cloned repository
- **package_name** (optional): Python package name — the skill will locate and clone the repository

At least one of the two must be provided. If `repo_path` is given and points to an
existing directory, skip straight to Step 2. Otherwise, use `package_name` to
discover and clone the repository.

## Step 1: Resolve Repository

If you already have a local repository path, skip to Step 2.

Otherwise, use the python-packaging-source-finder skill to locate the upstream
repository URL:

```text
Skill: python-packaging-source-finder
Args: <package_name>
```

If the skill returns a URL with high or medium confidence, clone it locally with
enough history for the git scan:

```bash
CLONE_DIR=$(mktemp -d -t security-audit-XXXXXX)
git clone --depth 50 -- "<repository_url>" "$CLONE_DIR/repo"
```

Use `$CLONE_DIR/repo` as the repo path for Steps 2 and 3.

If source-finder returns low confidence or no URL, stop and return a report with
risk rating `needs_review` and a note that the source repository could not be
located.

Clean up the clone when all phases are complete:

```bash
if [ -n "${CLONE_DIR}" ] && [[ "${CLONE_DIR}" == "${TMPDIR:-/tmp}"/* ]]; then
  rm -rf -- "${CLONE_DIR}"
else
  echo "ERROR: refusing to delete '${CLONE_DIR}' -- not under temp dir" >&2
fi
```

## Step 2: Hexora Static Analysis

Run the wrapper script which handles hexora installation and applies the tuned
rule exclusions:

```bash
./scripts/run-hexora.sh <repo-path>
```

Capture the JSON output. Each finding contains: rule code, file path, line number,
confidence level, and description. The wrapper filters out rules that are too noisy
for typical Python packages and sets a minimum confidence of `medium`. See the
script comments for the full exclusion list and rationale.

## Step 3: Git History Scan

If the repository path is not a git repository, skip this phase and note it in the report.

1. Determine the number of commits available and scan up to the last 50:

   ```bash
   git -C <repo-path> log -50 --format='%H'
   ```

2. From those commits, identify ones that modify supply-chain-sensitive files:
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

3. For each flagged commit, extract the diff and search for suspicious patterns:
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

4. Collect per finding: commit hash, author, date, file modified, and matching patterns.

## Step 4: AI Triage

Review all findings from Steps 2 and 3 in context. Read the relevant source files to understand the purpose of flagged code.

1. **Classify each hexora finding** as one of:
   - **Likely legitimate** — pattern is expected for the package's purpose (e.g., `subprocess` in a CLI tool)
   - **Suspicious** — pattern is unusual and warrants manual review (e.g., `base64` decode in `setup.py`)
   - **Critical** — pattern strongly indicates malicious intent (e.g., network exfiltration in install hooks)

2. **Review git history findings** — flag commits that introduced suspicious patterns into sensitive files. Consider whether the change is a normal dependency update or something unusual.

3. **Assign overall risk rating** based on the worst finding category:
   - **no_issues** — No findings from hexora or git history scan
   - **low_risk** — All findings classified as "likely legitimate"
   - **needs_review** — One or more findings classified as "suspicious"
   - **critical** — One or more findings classified as "critical"

## Output Format

Produce the following markdown report. When there are no findings, collapse to just the header, risk rating (`no_issues`), summary, and a note that no issues were found.

```markdown
# Security Assessment: {package-name}

**Risk Rating:** {no_issues | low_risk | needs_review | critical}
**Summary:** {1-2 sentence summary}

## Hexora Static Analysis

**Findings:** {N total} ({X critical, Y suspicious, Z likely legitimate})

### Critical Findings

| File | Line | Rule | Confidence | Description | Triage |
|------|------|------|------------|-------------|--------|
| setup.py | 42 | HX2000 | Very High | Base64 decode in install hook | Suspicious — no legitimate reason for encoded payloads in setup.py |

### Suspicious Findings

(same table format)

### Likely Legitimate

(same table format, brief — included for completeness but de-emphasized)

## Git History Analysis (Last 50 Commits)

**Commits touching sensitive files:** {N}

| Commit | Date | Author | File | Patterns Found |
|--------|------|--------|------|----------------|
| abc1234 | 2026-03-15 | user@example.com | setup.py | subprocess, os.system |

**AI Assessment:** {Brief narrative on whether the git history changes look normal or concerning, with reasoning}

## Recommendations

- {Bulleted list of specific actions}
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Source-finder returns low confidence or no URL | Stop; report `needs_review` with note that source repo could not be located |
| git clone fails | Stop; report `needs_review` with note that repo could not be cloned |
| Fewer than 50 commits | Scan all available commits |
| Hexora returns empty results | Report "no findings" for hexora section |
| No sensitive files modified in history | Report "no sensitive files found" in git history section |
| Path is not a git repository | Skip git history scan, note in report |
