---
name: python-packaging-binary-audit
description: Scan a Python package repository for compiled/binary files using Fromager-style detection and malcontent YARA analysis, then triage findings with deterministic rules and AI reasoning to produce a structured risk report section.
allowed-tools: Bash Read Grep
---

# Python Packaging Binary Audit

Scans a Python package repository for compiled or binary files using
Fromager-style extension and magic-header detection, then runs malcontent
YARA-based analysis on any detected binaries. Produces a self-contained
"Binary Scan" report section with triaged findings and a risk assessment.

## Inputs

- **repo_path** (required): Local filesystem path to an already-cloned repository

## Step 1: Detect Binaries

Run the binary scanner to find compiled files using Fromager-style extension and
magic-header detection:

```bash
STAGING_DIR=$(mktemp -d -t malcontent-staging-XXXXXX)
./scripts/scan_binaries.py --stage-to "$STAGING_DIR" "<repo-path>"
```

This outputs JSON to stdout with `total` and `findings` fields. Each finding has:
`path`, `match_type` (extension or magic_header), `suffix`, `size`, and optionally
`magic` (ELF, MachO, ar_archive, etc.).

The `--stage-to` flag copies detected binaries into a staging directory preserving
relative paths for malcontent analysis in the next step.

If the scanner finds **zero** binaries, skip to the Output section and note
"No binary files detected" in the report.

## Step 2: Run Malcontent

Run malcontent analysis on the staged binaries:

```bash
./scripts/run_malcontent.py "$STAGING_DIR"
```

This outputs JSON to stdout with malcontent's findings. The script expects the
native `mal` binary on PATH (or via `MALCONTENT_BIN` env var). If `mal` is not
available, it exits with code 2 — note this in the report as "malcontent
unavailable" and proceed with the binary scan findings only. Exit code 1
indicates a runtime error (timeout, invalid JSON, or execution failure).

## Step 3: Triage

Review binary findings in context. Read relevant source files to understand the
purpose of detected binaries. Triage proceeds in two stages: deterministic rules
first, then AI reasoning for anything unresolved.

### Stage 1 — Deterministic Rules

Apply the following rules **before** any AI reasoning. These handle the most
common clear-cut cases and make the triage reproducible.

| Condition | Verdict |
|-----------|---------|
| Binary is under `third_party/`, `vendor/`, or `extern/` **and** malcontent risk ≤ medium | PASS — vendored dependency |
| Binary is under `test/`, `tests/`, `benchmarks/`, or `examples/` **and** malcontent risk ≤ medium | PASS — test data |
| Binary suffix is `.ptx`, `.cubin`, `.fatbin`, or path contains `triton/` or `cuda` | PASS — GPU kernel |
| Malcontent risk is **critical** | BLOCK |
| Malcontent flags `remote_access`, `exfiltration`, or `backdoor` capabilities | BLOCK |
| Binary has no malcontent findings **and** is only detected by extension/magic header | PASS — opaque-only |
| Malcontent timed out | REVIEW — partial results, manual inspection recommended |

When multiple findings produce different verdicts, the overall precedence is
**BLOCK > REVIEW > PASS** — the most severe verdict wins.

Any finding not resolved by Stage 1 proceeds to Stage 2.

### Stage 2 — AI Reasoning

For findings that remain unresolved after deterministic rules, classify each as:

- **Likely legitimate** — binary is a known build artifact (e.g., pre-compiled protobuf, CUDA kernel)
- **Suspicious** — binary has unusual capabilities for the package context (e.g., network access in a math library)
- **Critical** — binary has capabilities strongly indicating malicious intent (e.g., backdoor, data exfiltration)

## Step 4: Cleanup

Remove the staging directory when analysis is complete:

```bash
if [ -n "${STAGING_DIR}" ] && [ -d "${STAGING_DIR}" ]; then
  rm -rf -- "${STAGING_DIR}"
fi
```

## Output Format

Produce the following markdown section:

```markdown
## Binary Scan

**Binaries detected:** {N}
**Malcontent status:** {ran successfully | unavailable — findings based on binary scan only | timed out — partial results}

### BLOCK Findings

| File | Type | Size | Malcontent Risk | Capabilities | Triage |
|------|------|------|-----------------|--------------|--------|
| src/lib/backdoor.so | ELF | 24KB | critical | remote_access, exfiltration | BLOCK — critical risk with network capabilities |

### REVIEW Findings

(same table format)

### PASS Findings

(same table format, brief — included for completeness but de-emphasized)
```

Also return a **risk_rating** value for this phase:

- **no_issues** — No binary files detected
- **low_risk** — All findings classified as "likely legitimate" or PASS
- **needs_review** — One or more findings classified as "suspicious" or REVIEW
- **critical** — One or more findings classified as "critical" or BLOCK

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Binary scan finds zero binaries | Note "No binary files detected", risk_rating = no_issues |
| Malcontent unavailable (exit code 2) | Triage binary findings using scan metadata only (extension, magic header, size); note malcontent was unavailable |
| Malcontent times out (exit code 1) | Report partial results; note timeout; REVIEW verdict for affected binaries |
| Malcontent produces invalid JSON (exit code 1) | Triage binary findings using scan metadata only; note malcontent output error |
