---
name: oci-cve-checker
description: Compare CVE vulnerabilities between two OCI container images and generate reports showing fixed and new CVEs.
allowed-tools: Bash Read
---

# OCI CVE Checker

This skill compares CVE vulnerabilities between two OCI container images and generates detailed reports showing which CVEs were fixed and which new CVEs were introduced.

## Instructions

When a user asks to compare CVEs between container images or analyze security differences:

1. **Check and install required dependencies**:
   ```bash
   ./scripts/manage_deps.sh
   ```
   This script checks for trivy, jq, and skopeo, and automatically installs any missing tools to a temporary directory if needed.

2. **Run the CVE comparison script** with two container image references:
   ```bash
   ./scripts/check_cves.sh <base_image> <target_image> [output_directory]
   ```

3. **Analyze the generated output files**:

   ### Output Files
   The script generates the following files in the output directory (default: `./cve-reports/`):

   - **`fixed_cves.txt`**: CVEs that existed in the base image but are fixed in the target image
   - **`new_cves.txt`**: New CVEs that appear in the target image but weren't in the base image
   - **`common_cves.txt`**: CVEs that exist in both images
   - **`summary.txt`**: High-level summary with counts and statistics
   - **`<image_name>_<digest>.json`**: Complete vulnerability scans for each image (filenames include image name and first 12 characters of digest, e.g., `python-3.11_a1b2c3d4e5f6.json`)

4. **Interpret the results** for the user:

   ### Fixed CVEs Analysis
   - Count of CVEs resolved between versions
   - Severity breakdown of fixed vulnerabilities
   - Notable security improvements
   - Packages that were updated to fix vulnerabilities

   ### New CVEs Analysis
   - Count of newly introduced CVEs
   - Severity assessment of new vulnerabilities
   - Risk evaluation for production deployment
   - Packages introducing new vulnerabilities
   - Recommendations for mitigation

   ### Overall Security Posture
   - Net change in vulnerability count
   - Severity trends (more/fewer critical CVEs)
   - Recommendation on whether to upgrade
   - Additional security considerations

## Usage Examples

### Compare Two Container Images
```bash
./scripts/check_cves.sh registry.io/app:v1.0 registry.io/app:v1.1
```
**Interpretation**: Compare CVEs between version 1.0 and 1.1, identifying security improvements and any regressions.

### Compare with Custom Output Directory
```bash
./scripts/check_cves.sh quay.io/myapp:latest quay.io/myapp:dev ./security-audit
```
**Interpretation**: Generate comparison reports in a custom directory for documentation or CI/CD integration.

### Compare Different Registries
```bash
./scripts/check_cves.sh docker.io/library/python:3.11 docker.io/library/python:3.12
```
**Interpretation**: Analyze security differences between Python base image versions.

### Private Registry Authentication
```bash
# Method 1: Using auth.json file (Recommended)
REGISTRY_AUTH_FILE=/home/default/containers/auth.json \
./scripts/check_cves.sh private-registry.io/app:v1 private-registry.io/app:v2

# Method 2: Using environment variables
TRIVY_USERNAME=myuser TRIVY_PASSWORD=mypass \
./scripts/check_cves.sh private-registry.io/app:v1 private-registry.io/app:v2

# Method 3: Trivy automatically uses podman credentials from ${XDG_RUNTIME_DIR}/containers/auth.json
podman login private-registry.io
./scripts/check_cves.sh private-registry.io/app:v1 private-registry.io/app:v2

# Method 4: For non-SSL registries
TRIVY_NON_SSL=true REGISTRY_AUTH_FILE=/home/default/containers/auth.json \
./scripts/check_cves.sh insecure-registry.io/app:v1 insecure-registry.io/app:v2
```
**Interpretation**: Trivy can authenticate to private registries using the REGISTRY_AUTH_FILE environment variable pointing to your auth.json, or using TRIVY_USERNAME/TRIVY_PASSWORD environment variables, or existing podman credentials.

## Key Analysis Points

### When Reviewing Fixed CVEs
- **Critical/High Severity Fixes**: Highlight major security improvements
- **Long-standing Vulnerabilities**: Note fixes for older, known issues
- **Completeness**: Check if all expected CVEs were addressed
- **Verification**: Confirm fixes align with release notes

### When Reviewing New CVEs
- **Severity Assessment**: Prioritize by CVSS score and exploitability
- **Exposure Analysis**: Determine if vulnerable code paths are reachable
- **Mitigation Options**: Suggest workarounds if immediate fix isn't available
- **Timeline**: Check if patches are available or planned

### Security Recommendations

Based on the comparison, provide guidance:

#### For Improved Security (More Fixed than New)
- "Upgrading is recommended - net reduction of X vulnerabilities"
- "Y critical CVEs fixed with only Z new low-severity issues"
- "Security posture improved, safe to deploy after testing"

#### For Degraded Security (More New than Fixed)
- "Caution: X new vulnerabilities introduced"
- "Review new CVEs before deploying to production"
- "Consider waiting for next release or apply mitigations"

#### For Mixed Results
- "Security trade-offs detected"
- "Fixed: [critical issues], but introduced: [new concerns]"
- "Recommend risk assessment based on your threat model"

## Tool Requirements

This skill requires the following tools to be installed:
- **trivy**: Container vulnerability scanner
- **jq**: JSON processor for parsing scan results
- **skopeo**: For image inspection and pre-validation (validates image tags exist before analysis)

## Error Handling

If the dependency check fails:
- **Missing tools**: Run `./scripts/manage_deps.sh` first to check and install trivy, jq, and skopeo
- **Auto-install failure**: Install tools manually as instructed by the manage_deps script

If the comparison script fails:
- **Image not found**: Verify image names and registry accessibility
- **Authentication required**: Set `TRIVY_USERNAME`/`TRIVY_PASSWORD` environment variables, or login with `podman login <registry>`
- **Network issues**: Check connectivity to container registries
- **Insufficient permissions**: Verify file write permissions for output directory
- **Non-SSL registry**: Set `TRIVY_NON_SSL=true` for insecure registries

## Integration Notes

This skill works well with:
- **CI/CD pipelines**: Automated security checks before deployment
- **Security audits**: Regular vulnerability assessments
- **Release validation**: Verify security improvements in new releases
- **Container image promotion**: Gate promotions based on CVE thresholds
- **K8s/OpenShift deployments**: Pre-deployment security validation

## Example Workflow

1. Developer builds new container image
2. Run CVE checker comparing old vs new image
3. Review fixed and new CVEs
4. Make deployment decision based on security posture
5. Document findings in security reports
6. Update deployment runbooks with any new mitigations
