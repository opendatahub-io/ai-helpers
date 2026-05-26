---
name: python-packaging-static-audit
description: Run hexora static analysis on a Python package repository to detect suspicious code patterns, then triage findings with deterministic rules and AI reasoning to produce a structured risk report section.
allowed-tools: Bash Read Grep
---

# Python Packaging Static Audit

Runs hexora static analysis on a Python package repository to detect suspicious
code patterns such as code execution, encoding/serialization, and native code
usage. Produces a self-contained "Hexora Static Analysis" report section with
triaged findings and a risk assessment.

## Inputs

- **repo_path** (required): Local filesystem path to an already-cloned repository

## Step 1: Run Hexora

Run the wrapper script which handles hexora installation and applies the tuned
rule exclusions:

```bash
./scripts/run-hexora.sh <repo-path>
```

Capture the JSON output. Each finding contains: rule code, file path, line number,
confidence level, and description. The wrapper filters out rules that are too noisy
for typical Python packages and sets a minimum confidence of `medium`. See the
script comments for the full exclusion list and rationale.

## Step 2: Triage

Review hexora findings in context. Read the relevant source files to understand
the purpose of flagged code. Triage proceeds in two stages: deterministic rules
first, then AI reasoning for anything unresolved.

### Stage 1 — Deterministic Rules

Apply the following rules **before** any AI reasoning. These handle the most
common clear-cut cases and make the triage reproducible.

| Condition | Verdict |
|-----------|---------|
| Finding is in a file under `test/`, `tests/`, `benchmarks/`, or `examples/` | PASS |
| Finding references a standard-library import already excluded by `run-hexora.sh` rule set | PASS |
| Finding is in `setup.py`, `setup.cfg`, or `pyproject.toml` **and** involves `eval`, `exec`, `compile`, `base64`, or `marshal` | REVIEW |

When multiple findings produce different verdicts, the overall precedence is
**BLOCK > REVIEW > PASS** — the most severe verdict wins.

Any finding not resolved by Stage 1 proceeds to Stage 2.

### Stage 2 — AI Reasoning

For findings that remain unresolved after deterministic rules, classify each as:

- **Likely legitimate** — pattern is expected for the package's purpose (e.g., `subprocess` in a CLI tool)
- **Suspicious** — pattern is unusual and warrants manual review (e.g., `base64` decode in `setup.py`)
- **Critical** — pattern strongly indicates malicious intent (e.g., network exfiltration in install hooks)

## Output Format

Produce the following markdown section:

```markdown
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
```

Also return a **risk_rating** value for this phase:

- **no_issues** — No hexora findings
- **low_risk** — All findings classified as "likely legitimate" or PASS
- **needs_review** — One or more findings classified as "suspicious" or REVIEW
- **critical** — One or more findings classified as "critical" or BLOCK

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Hexora returns empty results | Report "no findings" for hexora section, risk_rating = no_issues |
| Hexora is unavailable (`uvx` and `hexora` both missing) | Report hexora unavailable, risk_rating = needs_review |
