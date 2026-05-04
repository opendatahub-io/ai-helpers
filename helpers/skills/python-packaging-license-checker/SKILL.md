---
name: python-packaging-license-checker
description: Use this skill to check whether a Python package license is compatible with redistribution
  in Red Hat products, using the Fedora License Data as the authoritative policy source.
  Produces a structured six-field verdict with escalation guidance for non-trivial cases.
allowed-tools: Bash Skill WebFetch
---

# Python Package License Compatibility Checker

Evaluate whether a Python package license permits redistribution in Red Hat products.

**Policy basis**: Red Hat redistribution policy follows the Fedora Linux license
policy. Use the Fedora License Data as the authoritative source -- NOT OSI-approval
status.

## Inputs

- **package_name**: Python package name
- **repo_url**: upstream repository URL (if already known — skip the source-finder step and clone this directly)
- **source_available**: whether buildable source exists (if already known)
- **upstream_org**: name and primary country of the maintaining organisation (if already known)

## Step 1: Locate and clone the source repository

If a `repo_url` is provided, skip the source-finder step and use the provided URL directly with the git-shallow-clone skill.

Otherwise, use the python-packaging-source-finder skill to find the upstream repo URL:

```text
Skill: python-packaging-source-finder
```

Then use the git-shallow-clone skill to clone the repository locally:

```text
Skill: git-shallow-clone
```

This gives a local path to the cloned repo for deterministic license inspection.

## Step 2: Read the license from source

Search the cloned repo root for license files in this order:
LICENSE, LICENSE.txt, LICENSE.md, COPYING, COPYING.txt, LICENCE, LICENCE.txt

```bash
ls <clone_path>/{LICENSE,COPYING,LICENCE}{,.txt,.md} 2>/dev/null | head -1
```

Read the license file (up to 128 KB) and map to an SPDX identifier. If the file
exceeds 128 KB, read only the first 128 KB and note the truncation. If the file
cannot be read within 30 seconds, treat it as unreadable and set
Verdict: NEEDS-HUMAN-REVIEW with a note explaining the timeout.

Also check `pyproject.toml` or `setup.cfg` for a `license` field as a secondary
signal. If the PyPI metadata license differs from the source file, set
Source verified: MISMATCH (PyPI: [X], repo: [Y]) and use the source file as
authoritative.

**Normalise to SPDX ID** using exact then fuzzy matching:
- Deterministic: "Apache 2" -> Apache-2.0, "GPL v2" -> GPL-2.0-only,
  "MIT License" -> MIT, "LGPLv2.1" -> LGPL-2.1-only
- Ambiguous (do NOT auto-map): "BSD", "GPLv3" -> set NEEDS-HUMAN-REVIEW.
  These tokens map to multiple SPDX IDs; require human confirmation.

**Compound expressions**: If the license contains `AND` or `OR`:
- `AND`: split into components; every component must be individually allowed.
  If any single component is `not-allowed`, the whole expression is BLOCKED.
  Document the split in Notes.
- `OR`: evaluate each component; use the most permissive allowed one. If none are
  allowed, the overall verdict is the best individual verdict.

If no license file found and no SPDX mapping possible: Verdict: NEEDS-HUMAN-REVIEW.

Clean up the clone when done:

```bash
if [ -n "${CLONE_DIR}" ] && echo "${CLONE_DIR}" | grep -q '^/tmp/'; then
  rm -rf -- "${CLONE_DIR}"
else
  echo "ERROR: refusing to delete '${CLONE_DIR}' -- not under /tmp/" >&2
fi
```

## Step 3: Look up license in Fedora License Data

Fetch the live data:

```text
WebFetch: https://gitlab.com/fedora/legal/fedora-license-data/-/jobs/artifacts/main/raw/fedora-licenses.json?job=json
```

Search for an entry matching the SPDX ID (case-insensitive on `spdx_abbrev`).
Each entry has a `status` field which may be a string or an array. Normalise to
an array and apply the following deterministic mapping.

Fedora License Data defines these status values:

| Status | Meaning | Outcome |
|---|---|---|
| `allowed` | Approved for Fedora packages | Proceed to Step 4 |
| `allowed-fonts` | Approved only for font packages | Proceed to Step 4 (add note: "License approved for fonts only; verify component type") |
| `allowed-documentation` | Approved only for documentation | Proceed to Step 4 (add note: "License approved for documentation only; verify component type") |
| `allowed-content` | Approved only for content (non-code) | Proceed to Step 4 (add note: "License approved for content only; verify component type") |
| `not-allowed` | Explicitly prohibited | Verdict: BLOCKED |

Apply fail-closed logic:

- If any entry is `"not-allowed"` -> Verdict: BLOCKED
- If all entries are one of the `allowed*` statuses above (and none
  `"not-allowed"`) -> proceed to Step 4
- If the `status` field is missing, empty, or contains a value not listed in
  the table above -> Verdict: NEEDS-HUMAN-REVIEW (note the unrecognised value)
- SPDX ID not found in data -> Verdict: NEEDS-HUMAN-REVIEW

**Fallback table** (use only when the JSON fetch fails):

| Status | SPDX identifiers (representative) |
|---|---|
| allowed | MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, PSF-2.0, CC0-1.0 |
| allowed | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later |
| allowed | LGPL-2.0-only, LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-or-later |
| allowed | AGPL-3.0-only, AGPL-3.0-or-later, MPL-2.0, EUPL-1.2, EPL-2.0 |
| not-allowed | SSPL-1.0, BUSL-1.1, Commons-Clause |
| ESCALATE | Any custom/proprietary license not in SPDX |

When using fallback, append to Notes: "Fedora License Data unreachable; fallback
table used. Verify at https://docs.fedoraproject.org/en-US/legal/allowed-licenses/"

## Step 4: Verdict refinement (apply in order)

**Rule A -- Proprietary or custom license** (not in Fedora data):

First check the Vendor Agreements table below. If covered by an agreement:
Verdict: ALLOWED, Notes: "Covered by Red Hat [Vendor] redistribution agreement."

Otherwise:
- Red Hat / IBM-owned upstream (e.g. Neural Magic):
  Verdict: ESCALATE-TO-LEGAL.
  Notes: "Red Hat-owned proprietary license. Must be relicensed before inclusion.
  Open a ServiceNow opensource-legal ticket."
- Third-party proprietary:
  Verdict: ESCALATE-TO-LEGAL.
  Notes: "Third-party proprietary license. May be includable as a EULA-listed
  component. Open a legal-review task."

**Rule B -- AGPL-3.0** (status=allowed, SPDX is AGPL-3.0-only or -or-later):
Verdict: ALLOWED-WITH-CAVEAT.
Notes: "AGPL-3.0 is allowed for redistribution but is frequently part of a
dual-licensing strategy, increasing risk. PM sign-off required."

**Rule C -- All other allowed licenses**:
Verdict: ALLOWED. Notes: omit unless compliance note needed (e.g. LGPL dynamic
linking does not propagate copyleft).

**Rule D -- Not-allowed**:
Verdict: BLOCKED.
Notes: "License is on the Fedora not-allowed list."

## Step 5: Compliance checks

**Build compliance** (independent of license verdict):
If `source_available` is false or no buildable source exists (no setup.py,
pyproject.toml, or equivalent):
- Build compliance: BUILD-COMPLIANCE-FLAG
- Append to Notes: "No buildable source. Options: (1) request upstream sdist,
  (2) make dependency optional,
  (3) file PSX exception with 6-month deadline per PSS.SBR.02.02."
- Otherwise: Build compliance: OK

**Export compliance** (independent of license verdict):
Check the upstream org's primary country against these authoritative
machine-readable sources:
- US OFAC SDN List (XML):
  https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML
- EU Consolidated Sanctions (RSS/FSF):
  https://webgate.ec.europa.eu/europeaid/fsd/fsf/public/rss
- Red Hat geopolitical policy: consult exportcompliance@redhat.com

For each source checked, record the following metadata:
- `source_url`: the URL fetched
- `retrieved_at`: ISO 8601 timestamp of the fetch
- `fetch_outcome`: `success` or `failure`
- `retry_count`: number of retries attempted (0 if first attempt succeeded)

If flagged by any source:
- Export compliance: EXPORT-COMPLIANCE-FLAG
- Append to Notes: "Upstream org may require export compliance review. Contact
  exportcompliance@redhat.com. Source: <source_url>; Fetched: <retrieved_at>;
  Outcome: <fetch_outcome>; Retries: <retry_count>.
  Geopolitical sensitivity does not automatically block inclusion."

If sources are unreachable after 2 retries:
- Export compliance: EXPORT-COMPLIANCE-FLAG
- Append to Notes: "Export sanctions data unreachable (Retries: <retry_count>).
  _Verdict: NEEDS-HUMAN-REVIEW_"

Otherwise: Export compliance: OK

## Output Format

Produce ONLY this six-field block. No preamble, no extra text.

```text
_License:_ [SPDX expression, or "non-SPDX: [raw string]" if unmappable]
_Source verified:_ YES | NO | MISMATCH (PyPI: [X], repo: [Y])
_Verdict:_ ALLOWED | ALLOWED-WITH-CAVEAT | NEEDS-HUMAN-REVIEW | ESCALATE-TO-LEGAL | BLOCKED
_Build compliance:_ OK | BUILD-COMPLIANCE-FLAG
_Export compliance:_ OK | EXPORT-COMPLIANCE-FLAG
_Notes:_ [Actionable guidance. Omit if verdict is ALLOWED and all flags are OK.]
```

## Vendor Agreements

| Vendor | Covered components |
|---|---|
| NVIDIA | CUDA libraries, runtimes, NCCL, and related NVIDIA components |
| Intel Gaudi | Gaudi AI accelerator software and libraries |
| IBM Spyre | IBM Spyre AI hardware and associated software components |

## Quick Reference

| Scenario | Verdict | Build |
|---|---|---|
| MIT, Apache-2.0, `BSD-*`, ISC, PSF-2.0 | ALLOWED | OK |
| `GPL-*`, `LGPL-*` | ALLOWED | OK |
| `AGPL-3.0-*` | ALLOWED-WITH-CAVEAT | OK |
| SSPL-1.0, BUSL-1.1, Commons-Clause | BLOCKED | -- |
| RH-owned proprietary | ESCALATE-TO-LEGAL | -- |
| Third-party proprietary (no vendor agreement) | ESCALATE-TO-LEGAL | -- |
| PyPI/repo license mismatch | per repo license (MISMATCH noted) | OK |
| No buildable source | per license | FLAG |

## Error Handling

- **Fedora data unreachable**: Use fallback table; append note.
- **Source repo not found**: If python-packaging-source-finder returns null/low
  confidence, set Source verified: NO, verdict: NEEDS-HUMAN-REVIEW.
- **Source repo private/inaccessible**: Set Source verified: NO. Verdict:
  NEEDS-HUMAN-REVIEW.
- **Multiple conflicting LICENSE files**: Source verified: MISMATCH, verdict:
  NEEDS-HUMAN-REVIEW. Note the conflicting files.
