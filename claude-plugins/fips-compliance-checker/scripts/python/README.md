# Python FIPS 140-3 Compliance Scanner

Comprehensive FIPS 140-3 compliance scanner for Python applications on RHEL 9+.

## Overview

This scanner performs multi-layered analysis to ensure Python applications comply with FIPS 140-3 cryptographic requirements on Red Hat Enterprise Linux 9 or later. It scans dependencies, source code, runtime configuration, and provides actionable remediation guidance.

## Features

- **Multi-Layer Scanning**: 4 complementary scanning layers for comprehensive coverage
- **Context-Aware**: Distinguishes production vs test/example code
- **Rich Metadata**: Every finding includes severity, location, context, and remediation
- **Standalone & CI/CD Ready**: Works without Claude Code for automation
- **Bandit Integration**: Leverages industry-standard AST-based security analysis
- **False-Positive Detection**: Identifies legitimate non-security crypto usage

## Requirements

### Required
- Bash 4.0+
- `jq` (JSON processor)
- Container runtime: `podman` or `docker`

### Installation

```bash
# Install podman (recommended for RHEL/Fedora)
sudo dnf install podman

# Or install docker
# See https://docs.docker.com/get-docker/

# Install jq
sudo dnf install jq  # RHEL/Fedora
# or
sudo apt install jq  # Debian/Ubuntu

# Verify installation
podman --version
# or
docker --version
```

**Note**: The scanner uses Bandit in a container (`ghcr.io/pycqa/bandit/bandit:latest`). The image (~50MB) will be automatically pulled on first run.

## Usage

### Basic Usage

```bash
# Scan current directory
./scripts/python/scan-python-fips.sh

# Scan specific directory
./scripts/python/scan-python-fips.sh --path /path/to/project

# JSON output (default)
./scripts/python/scan-python-fips.sh --json > results.json

# Human-readable text output
./scripts/python/scan-python-fips.sh --text
```

### Advanced Options

```bash
# Exclude test and example code
./scripts/python/scan-python-fips.sh \
  --exclude 'tests/**' \
  --exclude 'examples/**'

# Use configuration file
./scripts/python/scan-python-fips.sh --config .fips-compliance.yaml

# Show help
./scripts/python/scan-python-fips.sh --help
```

## Scanning Layers

### Layer 1: Dependency Analysis
Scans Python dependency manifests for prohibited cryptographic packages:
- `requirements*.txt`
- `Pipfile` / `Pipfile.lock`
- `setup.py` / `setup.cfg`
- `pyproject.toml` / `poetry.lock`

**Detected Violations**:
- `pycrypto`, `PyCryptodome` (independent crypto implementations)
- `blake3`, `xxhash` (non-FIPS approved hash algorithms)
- `argon2`, `bcrypt`, `scrypt` (non-approved KDFs)

### Layer 2: Source Code Analysis (Bandit)
Uses Bandit for AST-based detection of cryptographic issues:
- B303: MD5 usage
- B304/B305: Insecure ciphers
- B311: Non-cryptographic random usage
- B324: hashlib configuration issues
- B501-B504: SSL/TLS configuration problems
- B505: Weak cryptographic keys

### Layer 3: Pattern Detection
Grep-based detection for patterns Bandit might miss:
- Direct crypto library imports (`from Crypto import`, `import blake3`)
- `random` module usage (should use `secrets`)
- MD5/SHA-1 with/without `usedforsecurity=False`
- Deprecated algorithm usage

### Layer 4: Runtime Verification
Checks Python runtime environment:
- Cryptography library FIPS status
- OpenSSL version (requires 3.x for RHEL 9)
- System vs bundled OpenSSL linkage
- Virtual environment detection

## Output Format

### JSON Schema

```json
{
  "metadata": {
    "scan_date": "2025-01-16T10:30:00Z",
    "scan_duration_seconds": 3.2,
    "target_path": "/path/to/project",
    "files_scanned": 45
  },
  "summary": {
    "total_findings": 5,
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 1,
    "production_critical": 2
  },
  "overall_status": "FAIL",
  "findings": [
    {
      "id": "DEP-001",
      "severity": "CRITICAL",
      "category": "DEPENDENCY",
      "status": "FAIL",
      "location": {
        "file": "requirements.txt",
        "line": 4,
        "package": "pycryptodome"
      },
      "detection": {
        "type": "PROHIBITED_PACKAGE",
        "name": "pycryptodome",
        "confidence": "HIGH"
      },
      "compliance": {
        "violation": "Non-FIPS approved cryptographic package",
        "fips_section": "140-3:7.5.1",
        "rhel_requirement": "Must use system-provided FIPS cryptographic module",
        "risk_profile": "CRYPTOGRAPHIC_BOUNDARY"
      },
      "context": {
        "file_path": "requirements.txt",
        "file_type": "dependency_manifest",
        "likely_production": true,
        "production_likelihood": 1.0
      },
      "remediation": {
        "action": "REMOVE",
        "priority": "IMMEDIATE",
        "effort": "MEDIUM",
        "recommendation": "Remove pycryptodome and use FIPS-compliant alternatives",
        "alternatives": ["cryptography>=41.0.0 (must link to system OpenSSL)"]
      }
    }
  ]
}
```

### Context Metadata

Every finding includes context metadata for intelligent filtering:

```json
{
  "context": {
    "file_path": "tests/test_crypto.py",
    "file_type": "test",
    "is_test_file": true,
    "is_example_file": false,
    "is_doc_file": false,
    "in_virtual_environment": false,
    "is_dev_dependency": false,
    "production_likelihood": 0.2,
    "likely_production": false
  }
}
```

## Exit Codes

- `0`: No violations found
- `1`: CRITICAL violations found
- `2`: HIGH violations found
- `3`: MEDIUM violations found
- `4`: Script error

## CI/CD Integration

### GitHub Actions

```yaml
name: FIPS Compliance Check

on: [push, pull_request]

jobs:
  fips-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y jq

      - name: Pull Bandit container image
        run: |
          docker pull ghcr.io/pycqa/bandit/bandit:latest

      - name: Run FIPS compliance scan
        run: |
          ./scripts/python/scan-python-fips.sh --json > fips-results.json

      - name: Check for critical violations
        run: |
          CRITICAL=$(jq -r '.summary.critical' fips-results.json)
          HIGH=$(jq -r '.summary.high' fips-results.json)

          if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
            echo "FIPS compliance violations found!"
            jq -r '.findings[] | select(.severity == "CRITICAL" or .severity == "HIGH")' fips-results.json
            exit 1
          fi

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: fips-compliance-report
          path: fips-results.json
```

### GitLab CI

```yaml
fips_compliance:
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add --no-cache bash jq
    - docker pull ghcr.io/pycqa/bandit/bandit:latest
  script:
    - ./scripts/python/scan-python-fips.sh --json > fips-results.json
    - |
      CRITICAL=$(jq -r '.summary.critical' fips-results.json)
      if [ "$CRITICAL" -gt 0 ]; then
        echo "CRITICAL FIPS violations found!"
        exit 1
      fi
  artifacts:
    paths:
      - fips-results.json
    when: always
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: fips-compliance
        name: FIPS 140-3 Compliance Check
        entry: scripts/python/scan-python-fips.sh
        args: ['--exclude', 'tests/**']
        language: system
        pass_filenames: false
        always_run: true
```

## Configuration File

Create `.fips-compliance.yaml` in your project root:

```yaml
scan:
  exclude:
    - tests/**
    - examples/**
    - docs/**

  # Report all findings but flag non-production code
  report_non_production: true

  # Minimum severity for non-zero exit code
  fail_on: high

context_rules:
  - pattern: "usedforsecurity=False"
    adjust_severity: low
    reason: "Non-security usage of hash function"

output:
  format: json
  verbosity: normal
  show_progress: true
```

## Interpreting Results

### Production vs Non-Production Findings

The scanner distinguishes production code from tests/examples:

- **Production Code** (`likely_production: true`):
  - Files in `src/`, `lib/`, `app/`
  - Main package files (`__init__.py`, `__main__.py`)
  - Configuration files

- **Non-Production Code** (`likely_production: false`):
  - Files in `tests/`, `examples/`, `docs/`
  - Virtual environment files
  - Build artifacts

**Recommendation**: Prioritize production findings, but fix test/example code to demonstrate best practices.

### False Positives

The scanner detects legitimate non-security crypto usage:

```python
# Correctly flagged as LOW severity
hashlib.md5(data, usedforsecurity=False)  # Checksums OK

# Incorrectly using MD5 for security - HIGH severity
hashlib.md5(password.encode())  # NOT OK for passwords
```

### Severity Levels

- **CRITICAL**: Direct FIPS boundary violations (bundled crypto, prohibited algorithms)
- **HIGH**: Security-critical operations with non-compliant algorithms
- **MEDIUM**: Approved algorithms without provider verification
- **LOW**: Configuration improvements, non-security usage

## Common Violations & Fixes

### Violation: pycryptodome in dependencies

```bash
# Before (CRITICAL)
pip install pycryptodome

# After (COMPLIANT)
pip install cryptography>=41.0.0
# Ensure it links to system OpenSSL
```

### Violation: MD5 for password hashing

```python
# Before (CRITICAL)
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()

# After (COMPLIANT)
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import secrets

salt = secrets.token_bytes(16)
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000
)
password_hash = kdf.derive(password.encode())
```

### Violation: random module for tokens

```python
# Before (HIGH)
import random
token = random.randint(0, 1000000)

# After (COMPLIANT)
import secrets
token = secrets.randbelow(1000001)
```

### Violation: MD5 for checksums

```python
# Before (HIGH - unmarked)
checksum = hashlib.md5(data).hexdigest()

# Option 1: Mark as non-security (LOW)
checksum = hashlib.md5(data, usedforsecurity=False).hexdigest()

# Option 2: Use approved algorithm (COMPLIANT)
checksum = hashlib.sha256(data).hexdigest()
```

## Runtime Verification

To verify FIPS compliance at runtime:

```bash
# Check system FIPS mode
fips-mode-setup --check

# Check cryptography library
python3 -c "from cryptography.hazmat.backends.openssl import backend; print('FIPS:', backend._fips_enabled)"

# Check OpenSSL provider
openssl list -providers

# Check crypto policy
update-crypto-policies --show
```

## Troubleshooting

### Container runtime not found

```bash
# Install podman (recommended for RHEL/Fedora)
sudo dnf install podman

# Or install docker
# See https://docs.docker.com/get-docker/

# Verify installation
podman --version
# or
docker --version
```

### Bandit container image pull fails

```bash
# Manually pull the image
podman pull ghcr.io/pycqa/bandit/bandit:latest
# or
docker pull ghcr.io/pycqa/bandit/bandit:latest

# For air-gapped environments, download and load the image:
# 1. On a connected system:
podman save -o bandit.tar ghcr.io/pycqa/bandit/bandit:latest
# 2. Transfer bandit.tar to air-gapped system
# 3. On air-gapped system:
podman load -i bandit.tar
```

### Permission denied

```bash
# Make scripts executable
chmod +x scripts/python/scan-python-fips.sh
chmod +x scripts/python/lib/*.sh
```

### jq not found

```bash
# Install jq
sudo dnf install jq  # RHEL/Fedora
sudo apt install jq  # Debian/Ubuntu
```

## Testing

Run the integration test suite:

```bash
# Run all tests
./tests/test-python-scanner.sh

# Expected output:
# ═══════════════════════════════════════════════
#  FIPS Python Scanner Integration Tests
# ═══════════════════════════════════════════════
#
# ✓ Scanner script exists and is executable
# ✓ Violating project scan detects violations
# ✓ Detects pycryptodome in dependencies
# ✓ Detects MD5 usage in source code
# ...
# All tests passed!
```

## References

- [FIPS 140-3 Standard](https://csrc.nist.gov/publications/detail/fips/140/3/final)
- [RHEL 9 FIPS Mode](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/security_hardening/assembly_installing-a-rhel-9-system-with-fips-mode-enabled_security-hardening)
- [Python cryptography library](https://cryptography.io/)
- [Bandit Security Linter](https://bandit.readthedocs.io/)

## License

Part of the FIPS Compliance Checker plugin for Claude Code.
