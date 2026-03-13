---
name: python-packaging-license-checker
description: Check whether a Python package license is compatible with redistribution
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
- **source_available**: whether buildable source exists (if already known)
- **upstream_org**: name and primary country of the maintaining organisation (if already known)

## Step 1: Locate and clone the source repository

Use the python-packaging-source-finder skill to find the upstream repo URL:

```
Skill: python-packaging-source-finder
```

Then use the git-shallow-clone skill to clone the repository locally:

```
Skill: git-shallow-clone
```

This gives a local path to the cloned repo for deterministic license inspection.

## Step 2: Read the license from source

Search the cloned repo root for license files in this order:
LICENSE, LICENSE.txt, LICENSE.md, COPYING, COPYING.txt, LICENCE, LICENCE.txt

```bash
find <clone_path> -maxdepth 1 -iname "license*" -o -iname "copying*" -o -iname "licence*" | head -5
```

Read the first 30 lines of the found file and map to an SPDX identifier.

Also check `pyproject.toml` or `setup.cfg` for a `license` field as a secondary
signal. If the PyPI metadata license differs from the source file, set
Source verified: MISMATCH (PyPI: [X], repo: [Y]) and use the source file as
authoritative.

**Normalise to SPDX ID** using exact then fuzzy matching:
- "Apache 2" -> Apache-2.0, "GPL v2" -> GPL-2.0-only, "BSD" -> BSD-3-Clause,
  "GPLv3" -> GPL-3.0-or-later, "MIT License" -> MIT, "LGPLv2.1" -> LGPL-2.1-only

**Compound expressions**: If the license contains `AND` or `OR`:
- `AND`: split and evaluate each component. Apply the license governing the
  importable library API (not a bundled CLI). Document the split in Notes.
- `OR`: evaluate each component; use the most permissive allowed one. If none are
  allowed, the overall verdict is the best individual verdict.

If no license file found and no SPDX mapping possible: Verdict: NEEDS-HUMAN-REVIEW.

Clean up the clone when done:

```bash
rm -rf <clone_parent_dir>
```

## Step 3: Look up license in Fedora License Data

Fetch the live data:

```
WebFetch: https://gitlab.com/fedora/legal/fedora-license-data/-/jobs/artifacts/main/raw/fedora-licenses.json?job=json
```

Search for an entry matching the SPDX ID (case-insensitive on `spdx_abbrev`).
Each entry has `status`: "allowed" or "not-allowed".

- `allowed` -> proceed to Step 4 (verdict refinement)
- `not-allowed` -> Verdict: BLOCKED
- not found -> Verdict: NEEDS-HUMAN-REVIEW

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
If upstream org's primary country is on the US OFAC sanctions list, EU Consolidated
Sanctions List, or flagged by Red Hat geopolitical policy:
- Export compliance: EXPORT-COMPLIANCE-FLAG
- Append to Notes: "Upstream org may require export compliance review. Contact
  exportcompliance@redhat.com. Geopolitical sensitivity does not automatically block
  inclusion (precedent: Yandex/Russia cleared for catboost)."
- Otherwise: Export compliance: OK

## Output Format

Produce ONLY this six-field block. No preamble, no extra text.

```
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

| Scenario | Verdict | Build | Export |
|---|---|---|---|
| MIT, Apache-2.0, BSD-*, ISC, PSF-2.0 | ALLOWED | OK | OK |
| GPL-*, LGPL-* | ALLOWED | OK | OK |
| AGPL-3.0-* | ALLOWED-WITH-CAVEAT | OK | OK |
| SSPL-1.0, BUSL-1.1, Commons-Clause | BLOCKED | -- | -- |
| RH-owned proprietary | ESCALATE-TO-LEGAL | -- | -- |
| Third-party proprietary (no vendor agreement) | ESCALATE-TO-LEGAL | -- | -- |
| PyPI/repo license mismatch | per repo license (MISMATCH noted) | OK | OK |
| No buildable source | per license | FLAG | OK |
| OFAC/sanctions-flagged upstream | per license | OK | FLAG |

## Error Handling

- **Fedora data unreachable**: Use fallback table; append note.
- **Source repo not found**: If python-packaging-source-finder returns null/low
  confidence, set Source verified: NO, verdict: NEEDS-HUMAN-REVIEW.
- **Source repo private/inaccessible**: Set Source verified: NO. Verdict:
  NEEDS-HUMAN-REVIEW.
- **Multiple conflicting LICENSE files**: Source verified: MISMATCH, verdict:
  NEEDS-HUMAN-REVIEW. Note the conflicting files.
