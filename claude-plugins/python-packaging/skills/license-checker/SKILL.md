---
name: license-checker
description: Assess license compatibility for Python package redistribution using SPDX.org license database. Evaluates whether a given license allows building and distributing wheels, with real-time license information lookup.
allowed-tools: [WebFetch]
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

3. **Risk Classification**:
   ```
   IF (isOsiApproved AND isFsfLibre AND permissive_pattern):
       Risk = Low, Status = Compatible
   ELIF (isOsiApproved AND weak_copyleft_pattern):
       Risk = Medium, Status = Compatible with Requirements
   ELIF (strong_copyleft_pattern OR NOT isOsiApproved):
       Risk = High, Status = Restricted/Incompatible
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

### Compatibility Assessment Logic

Use SPDX flags and license patterns to determine compatibility:

#### ✅ Highly Compatible (Low Risk)
- OSI Approved AND FSF Libre
- Permissive licenses (MIT, Apache, BSD, ISC family)
- No strong copyleft requirements

#### ⚠️ Compatible with Requirements (Medium Risk)
- OSI Approved but specific obligations
- Weak copyleft (LGPL, MPL)
- File-level copyleft licenses

#### ❌ Restricted/High Risk
- Strong copyleft (GPL, AGPL)
- Non-OSI approved licenses
- Proprietary or unclear terms

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
