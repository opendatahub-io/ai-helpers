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
- **output_file** (optional): Write the report section to this file path instead of
  returning it inline. The first line of the file must be `RISK_RATING:<value>` so
  the orchestrator can parse it without reading the full report.
- **hexora_results** (optional): File path to pre-computed hexora JSON output
  (`hexora-results.json`). Schema: `{status, total, findings[]}`. When provided,
  skip running `run-hexora.sh` and parse this file directly for triage. Status
  values: `"success"`, `"unavailable"`, `"timeout"`, `"error"`.

## Step 1: Obtain Hexora Results

### Option A - Pre-computed results (CI mode)

If `hexora_results` is provided and the file exists, read and parse it as JSON:

- If `status` is `"success"`: use the `findings` array as the hexora output.
  Each entry is a raw hexora JSONL object (rule, severity, file, line, etc.).
  Rules HX1000, HX1020, HX1030, HX3010, HX3040, HX5000-HX5050, HX6020-HX6060,
  HX7000-HX7020 are already excluded by the CI runner; minimum confidence is
  `medium`. Proceed directly to Step 2 (Triage).
- If `status` is `"unavailable"`, `"timeout"`, or `"error"`: skip to the Output
  section and produce the report with `risk_rating = needs_review`, noting the
  degraded status and any `error` message from the JSON. **Do not re-run hexora.**
  The CI runner already attempted execution under controlled conditions, and
  re-running in the agent container would likely hit the same failure.
- For any other `status` value not listed above: treat it as an error and report
  `risk_rating = needs_review`, noting the unrecognized status value.

### Option B - Run hexora locally (standalone mode)

If `hexora_results` is not provided, run the wrapper script which handles hexora
installation and applies the tuned rule exclusions:

```bash
./scripts/run-hexora.sh <repo-path>
hexora_exit=$?
```

Check the exit code before proceeding:

- **Exit 0**: hexora ran successfully. Capture the JSON output. Each finding
  contains: rule code, file path, line number, confidence level, and description.
- **Exit 2**: hexora is not installed and cannot be auto-installed via `uvx`.
  **Do not fail.** Skip to the Output section and produce the report with
  `risk_rating = needs_review` stating hexora was unavailable.
- **Exit 1**: hexora encountered a runtime error. Skip to the Output section
  and produce the report with `risk_rating = needs_review` noting the error.

The wrapper filters out rules that are too noisy for typical Python packages and
sets a minimum confidence of `medium`. See the script comments for the full
exclusion list and rationale.

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

The **risk_rating** for this phase is one of:

- **no_issues** — No hexora findings
- **low_risk** — All findings classified as "likely legitimate" or PASS
- **needs_review** — One or more findings classified as "suspicious" or REVIEW
- **critical** — One or more findings classified as "critical" or BLOCK

If `output_file` is provided, write the file with the first line as
`RISK_RATING:<value>` followed by a blank line and then the markdown section
above. If `output_file` is not provided, return the report section inline.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Hexora returns empty results | Report "no findings" for hexora section, risk_rating = no_issues |
| Hexora is unavailable (`uvx` and `hexora` both missing) | Report hexora unavailable, risk_rating = needs_review |
| Pre-computed `hexora_results` file path provided but file missing, unreadable, or invalid JSON | Report hexora unavailable, risk_rating = needs_review |
| Pre-computed `hexora_results` has degraded `status` (`unavailable`/`timeout`/`error`) | Do not re-run hexora; report the degraded status, risk_rating = needs_review |
