---
description: Scan project or container image for FIPS 140-3 compliance violations
---

Perform a comprehensive FIPS 140-3 compliance audit for containerized applications running on Red Hat Enterprise Linux 9 (or later).

{?image:Container image reference (optional, e.g., quay.io/myorg/myapp:latest)}

Launch the fips-compliance-checker:fips-compliance-checker agent to conduct a thorough security analysis {?image:of the container image `{image}`:of the current project}, scanning for:

- Non-compliant cryptographic libraries and dependencies
- Prohibited or deprecated algorithms (MD5, SHA-1, DES, 3DES, RC4, etc.)
- Non-FIPS approved algorithms (Blake3, ChaCha20, Curve25519, etc.)
- Cryptographic operations that bypass RHEL's FIPS-certified boundary
- Configuration issues affecting FIPS compliance
- Container base image compliance
- Build system settings that may impact FIPS mode

The agent will provide:
- Detailed compliance report with severity levels (CRITICAL, HIGH, MEDIUM, LOW)
- Specific file locations and line numbers for violations
- Actionable remediation steps with code examples
- Compliance score breakdown
- Verification commands to confirm compliance

Use the Task tool with subagent_type="fips-compliance-checker:fips-compliance-checker" to perform this analysis.
