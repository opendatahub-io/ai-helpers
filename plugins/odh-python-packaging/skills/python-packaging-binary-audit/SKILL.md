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
- **output_file** (optional): Write the report section to this file path instead of
  returning it inline. The first line of the file must be `RISK_RATING:<value>` so
  the orchestrator can parse it without reading the full report.
- **binary_scan** (optional): File path to pre-computed binary scanner JSON output
  (`binary-scan.json`). Schema: `{total, findings[{path, match_type, suffix, size,
  magic?}]}`. When provided, skip running `scan_binaries.py`.
- **malcontent_results** (optional): File path to pre-computed malcontent JSON
  output (`malcontent-results.json`). Schema: `{status, Files?}`. Status values:
  `"success"`, `"unavailable"`, `"timeout"`, `"failed"`, `"invalid"`, `"skipped"`.
  When provided, skip running `run_malcontent.py`.

## Step 1: Obtain Binary Scan Results

### Option A - Pre-computed results (CI mode)

If `binary_scan` is provided and the file exists, read and parse it as JSON.
Use the `total` and `findings` fields directly. Skip running `scan_binaries.py`
and skip creating the staging directory (STAGING_DIR) since binaries are already
analyzed. Each finding has: `path` (relative to repo root), `match_type`
(`"extension"` or `"magic_header"`), `suffix`, `size`, and optionally `magic`
(ELF, MachO, ar_archive, etc.).

If `total` is 0, skip to the Output section and note "No binary files detected"
in the report.

### Option B - Run binary scanner locally (standalone mode)

If `binary_scan` is not provided, run the binary scanner to find compiled files
using Fromager-style extension and magic-header detection:

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

## Step 2: Obtain Malcontent Results

### Option A - Pre-computed results (CI mode)

If `malcontent_results` is provided and the file exists, read and parse it as JSON:

- If `status` is `"success"`: use the `Files` dict as malcontent output (keyed by
  file path, native malcontent `--format json` structure). Proceed to Step 3
  (Triage).
- If `status` is `"unavailable"`, `"timeout"`, `"failed"`, or `"invalid"`:
  treat malcontent as unavailable. **Do not re-run malcontent.** The CI runner
  already attempted execution under controlled conditions, and re-running in the
  agent container would likely hit the same failure. Proceed to
  triage using only the binary scan metadata (extension, magic header, size).
  Note the degraded status and any `error` message from the JSON in the report.
- If `status` is `"skipped"`: no binaries were detected upstream. If
  `binary_scan.total == 0`, this is consistent; skip to Output. If
  `binary_scan.total > 0`, this is a data inconsistency from the CI pipeline.
  treat malcontent as unavailable and triage using binary scan metadata only;
  note the inconsistency in the report.
- For any other `status` value not listed above: treat malcontent as unavailable
  and triage using binary scan metadata only, noting the unrecognized status.

### Mixed mode - binary_scan only

If `malcontent_results` is NOT provided but `binary_scan` WAS provided, treat
malcontent as unavailable and triage using binary scan metadata only.

### Option B - Run malcontent locally (standalone mode)

If neither `binary_scan` nor `malcontent_results` is provided, run malcontent
analysis on the staged binaries:

```bash
./scripts/run_malcontent.py "$STAGING_DIR"
malcontent_exit=$?
```

Check the exit code before proceeding:

- **Exit 0**: malcontent ran successfully. Capture the JSON output with findings.
- **Exit 2**: malcontent (`mal`) is not installed. **Do not fail.** Proceed to
  triage using only the binary scan metadata (extension, magic header, size).
  Note "malcontent unavailable" in the report output.
- **Exit 1**: malcontent encountered a runtime error (timeout, invalid JSON, or
  execution failure). **Do not fail.** Proceed to triage using only the binary
  scan metadata. Note the error in the report output.

When malcontent is unavailable or fails, the binary scan findings alone still
provide value — file paths, types, and sizes are sufficient for the deterministic
triage rules that do not depend on malcontent risk levels.

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

Remove the staging directory if it was created (Step 1 Option B). When both
`binary_scan` and `malcontent_results` were pre-computed, no STAGING_DIR exists
and this step is a no-op.

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

The **risk_rating** for this phase is one of:

- **no_issues** — No binary files detected
- **low_risk** — All findings classified as "likely legitimate" or PASS
- **needs_review** — One or more findings classified as "suspicious" or REVIEW
- **critical** — One or more findings classified as "critical" or BLOCK

If `output_file` is provided, write the file with the first line as
`RISK_RATING:<value>` followed by a blank line and then the markdown section
above. If `output_file` is not provided, return the report section inline.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Binary scan finds zero binaries | Note "No binary files detected", risk_rating = no_issues |
| Malcontent unavailable (exit code 2) | Triage binary findings using scan metadata only (extension, magic header, size); note malcontent was unavailable |
| Malcontent times out (exit code 1) | Report partial results; note timeout; REVIEW verdict for affected binaries |
| Malcontent produces invalid JSON (exit code 1) | Triage binary findings using scan metadata only; note malcontent output error |
| Pre-computed `binary_scan` file path provided but file missing, unreadable, or invalid JSON | Report binary scan unavailable, risk_rating = needs_review |
| Pre-computed `malcontent_results` file path provided but file missing, unreadable, or invalid JSON | Proceed with binary scan metadata only; note malcontent output error |
| Pre-computed `malcontent_results` has degraded `status` (`unavailable`/`timeout`/`failed`/`invalid`) | Do not re-run malcontent; triage with binary scan metadata only; note the degraded status |
| Pre-computed `malcontent_results` has `status` `"skipped"` but `binary_scan.total > 0` | Data inconsistency; treat malcontent as unavailable; triage with binary scan metadata; note inconsistency |
