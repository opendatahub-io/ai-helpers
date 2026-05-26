---
name: python-packaging-security-audit
description: Use this skill to evaluate the security of a Python package repository by orchestrating static analysis, binary scanning, and git history inspection sub-skills in parallel, then combining their results into a unified security report with a risk rating.
allowed-tools: Bash Read Grep Skill
---

# Python Packaging Security Audit

Orchestrates a comprehensive pre-onboarding security evaluation of Python
packages by dispatching three specialized sub-skills as parallel background
agents. Each agent writes its report section to an individual file; the
orchestrator reads all files and assembles the unified report.

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

Use `$CLONE_DIR/repo` as the repo path for Step 2.

If source-finder returns low confidence or no URL, stop and return a report with
risk rating `needs_review` stating that the source repository could not be
located.

## Step 2: Dispatch Parallel Audits

Create a working directory for the report files:

```bash
AUDIT_DIR=$(mktemp -d -t security-audit-results-XXXXXX)
```

Dispatch three background agents **in parallel**. Each agent invokes one sub-skill
and writes its findings to an individual file. The orchestrator does not need the
intermediate reasoning context — only the final report sections matter.

**Agent 1 — Static Analysis:**

```text
Dispatch a background Agent that invokes the python-packaging-static-audit skill
with repo_path=<repo-path> and output_file=$AUDIT_DIR/static-audit.md, then exits.
```

**Agent 2 — Binary Scan:**

```text
Dispatch a background Agent that invokes the python-packaging-binary-audit skill
with repo_path=<repo-path> and output_file=$AUDIT_DIR/binary-audit.md, then exits.
```

**Agent 3 — Git History:**

```text
Dispatch a background Agent that invokes the python-packaging-git-audit skill
with repo_path=<repo-path> and output_file=$AUDIT_DIR/git-audit.md, then exits.
```

Wait for all three agents to complete before proceeding.

## Step 3: Combine Results

Read each output file. The first line of each file contains `RISK_RATING:<value>`.
Extract the risk rating and the markdown report section from each file.

If a file is missing or empty, treat that phase as `risk_rating = needs_review`
and state in the report section that the sub-skill did not produce output.

Assign the **overall risk rating** as the worst (most severe) rating across all
phases:

- **no_issues** — All sub-skills returned no_issues
- **low_risk** — Worst sub-skill rating is low_risk
- **needs_review** — At least one sub-skill returned needs_review
- **critical** — At least one sub-skill returned critical

Precedence: **critical > needs_review > low_risk > no_issues**

## Step 4: Cleanup

Clean up temporary directories:

```bash
rm -rf -- "${AUDIT_DIR}"

if [ -n "${CLONE_DIR}" ] && [[ "${CLONE_DIR}" == "${TMPDIR:-/tmp}"/* ]]; then
  rm -rf -- "${CLONE_DIR}"
else
  echo "ERROR: refusing to delete '${CLONE_DIR}' -- not under temp dir" >&2
fi
```

## Output Format

Produce the following markdown report. When there are no findings, collapse to just
the header, risk rating (`no_issues`), summary, and a statement that no issues were found.

```markdown
# Security Assessment: {package-name}

**Risk Rating:** {no_issues | low_risk | needs_review | critical}
**Summary:** {1-2 sentence summary}

{Hexora Static Analysis section from static-audit.md}

{Binary Scan section from binary-audit.md}

{Git History Analysis section from git-audit.md}

## Recommendations

- {Bulleted list of specific actions based on findings across all phases}
```

## Error Handling

**Never abort the audit because a single tool is missing.** Each sub-skill
handles missing tools (hexora, malcontent) by returning a degraded report
section with `risk_rating = needs_review` instead of failing. The orchestrator
must always dispatch all three agents and combine whatever results are available.

| Scenario | Behavior |
|----------|----------|
| Source-finder returns low confidence or no URL | Stop; report `needs_review` stating source repo could not be located |
| git clone fails | Stop; report `needs_review` stating repo could not be cloned |
| A sub-skill output file is missing or empty | Include a note in that section; treat that phase as `needs_review` |
| A sub-skill reports tool unavailable | Include its degraded output in the report; treat that phase as `needs_review` |
| All sub-skills return no_issues | Report overall `no_issues` |
