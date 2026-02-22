---
name: python-packaging-license-checker
description: Assess license compatibility for Python package redistribution using SPDX.org license database. Evaluates whether a given license allows building and distributing wheels, with real-time license information lookup.
allowed-tools: WebFetch
---

# Python Package License Compatibility Checker

This skill helps you evaluate whether a Python package license is compatible with redistribution, particularly for building and distributing wheels in enterprise environments. It uses the authoritative SPDX License List for accurate, up-to-date license information.

## Assessment Instructions

When a user provides a license name and asks about compatibility for redistribution, building wheels, or licensing restrictions, follow this methodology:

### Step-by-Step Process

1. **Fetch Current SPDX Data**:
   ```
   Use WebFetch to query: https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json
   ```

2. **License Matching**:
   - Try exact SPDX ID match first
   - Try case-insensitive SPDX ID match
   - Try full name matching
   - Try partial/fuzzy matching for common variations

3. **Risk Classification** (check strong copyleft FIRST to prevent misclassification):
   ```
   IF (strong_copyleft_pattern):
       Risk = High, Status = Restricted/Incompatible
       # GPL, AGPL are ALWAYS restricted regardless of OSI/FSF status
   ELIF (NOT isOsiApproved):
       Risk = High, Status = Restricted/Incompatible
   ELIF (isOsiApproved AND weak_copyleft_pattern):
       Risk = Medium, Status = Compatible with Requirements
   ELIF (isOsiApproved AND isFsfLibre AND permissive_pattern):
       Risk = Low, Status = Compatible
   ELSE:
       Risk = High, Status = Unknown - requires manual review
   ```

4. **Generate Assessment**:
   - Include all SPDX metadata
   - Provide clear compatibility guidance
   - List specific requirements
   - Add Red Hat context where relevant

## License Assessment Framework

### Input Processing
Accept various formats and normalize them:
- **SPDX Identifiers**: "MIT", "Apache-2.0", "GPL-3.0-only"
- **Full Names**: "MIT License", "Apache License 2.0", "GNU General Public License v3.0"
- **Common Aliases**: "Apache 2", "BSD 3-Clause", "GPLv3"
- **Case Variations**: Handle case-insensitive matching

### SPDX Data Analysis
When processing SPDX license data, examine these key fields:
- `licenseId`: Official SPDX identifier
- `name`: Full license name
- `isOsiApproved`: OSI approval status (boolean)
- `isFsfLibre`: FSF Free Software status (boolean)
- `isDeprecatedLicenseId`: Whether license is deprecated (boolean)
- `reference`: URL to full license details
- `seeAlso`: Array of additional reference URLs

### License Pattern Definitions

Use these explicit pattern lists for classification. Match against the SPDX `licenseId` field (case-insensitive).

#### Permissive Patterns (permissive_pattern)
Licenses where the `licenseId` contains or matches any of:
- `MIT`, `Apache-`, `BSD-`, `ISC`, `Unlicense`, `0BSD`, `PSF-`, `Python-`, `Zlib`, `BSL-1.0`, `CC0-`, `WTFPL`, `MulanPSL-`

#### Weak Copyleft Patterns (weak_copyleft_pattern)
Licenses where the `licenseId` contains or matches any of:
- `LGPL-`, `MPL-`, `EPL-`, `CDDL-`, `CPL-`, `CeCILL-2.1`, `EUPL-`

#### Strong Copyleft Patterns (strong_copyleft_pattern)
Licenses where the `licenseId` contains or matches any of:
- `GPL-` (but NOT `LGPL-`), `AGPL-`, `SSPL-`, `OSL-`, `CeCILL-` (but NOT `CeCILL-2.1`), `EUPL-` (when used with strong copyleft intent)

**CRITICAL**: `GPL-2.0`, `GPL-3.0`, `GPL-2.0-only`, `GPL-2.0-or-later`, `GPL-3.0-only`, `GPL-3.0-or-later` are ALL strong copyleft. They are NOT permissive. They MUST be classified as Restricted/Incompatible for commercial wheel redistribution.

### Compatibility Assessment Logic

Use SPDX flags and the pattern definitions above to determine compatibility:

#### ✅ Highly Compatible (Low Risk)
- OSI Approved AND FSF Libre AND matches permissive_pattern
- Examples: MIT, Apache-2.0, BSD-3-Clause, ISC, PSF-2.0
- No copyleft requirements of any kind

#### ⚠️ Compatible with Requirements (Medium Risk)
- OSI Approved AND matches weak_copyleft_pattern
- Examples: LGPL-2.1-only, LGPL-3.0-or-later, MPL-2.0
- File-level or library-level copyleft only

#### ❌ Restricted/High Risk
- Matches strong_copyleft_pattern (GPL, AGPL) — regardless of OSI or FSF status
- Non-OSI approved licenses
- Proprietary or unclear terms
- GPL licenses require ALL derivative works to be released under the same GPL license, making them incompatible with proprietary or commercial redistribution of binary wheels

### Output Format

Provide a structured assessment with:

1. **SPDX Information**:
   - Official SPDX ID
   - Full license name
   - OSI Approved: Yes/No
   - FSF Libre: Yes/No
   - Deprecated: Yes/No (if applicable)

2. **Compatibility Assessment**:
   - Status: Compatible/Restricted/Incompatible
   - Redistribution: Allowed/Restricted/Prohibited
   - Commercial Use: Allowed/Restricted/Prohibited

3. **Requirements**: Key compliance obligations
4. **Risk Level**: Low/Medium/High for enterprise use
5. **Red Hat Context**: Special considerations if applicable


## Red Hat Vendor Agreements

Red Hat has specific licensing agreements with the following hardware vendors:

- **NVIDIA**: Agreement covers CUDA libraries, runtimes, and related NVIDIA proprietary components
- **Intel Gaudi**: Agreement covers Gaudi AI accelerator software and libraries
- **IBM Spyre**: Agreement covers IBM Spyre AI hardware and associated software components

When evaluating packages with dependencies on these vendor-specific components, note that Red Hat has explicit redistribution rights under these agreements.

## Error Handling

### SPDX Data Fetch Failures
If the SPDX license list cannot be retrieved, exit early and warn the user.

### License Not Found in SPDX
When a license identifier is not found in the SPDX license list:
1. Check for common typos or variations
2. Suggest SPDX-compliant alternatives
3. Recommend contacting package maintainer
4. Provide conservative risk assessment

### Deprecated Licenses
For deprecated SPDX licenses:
1. Note the deprecation status
2. Suggest migrating to current equivalent
3. Provide assessment based on deprecated license terms
4. Recommend updating package licensing

For complex licensing scenarios involving multiple packages or custom license terms, recommend consultation with legal counsel.

## Integration Notes

This skill works best when combined with:
- **python-packaging-license-finder** - Use to find license names before compatibility assessment
