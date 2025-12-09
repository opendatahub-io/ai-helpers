# FIPS 140-3 Compliance Checker

A Claude Code plugin that provides comprehensive FIPS 140-3 compliance auditing for containerized applications running on Red Hat Enterprise Linux 9 (or later).

## Overview

This plugin helps ensure your applications meet FIPS 140-3 cryptographic compliance requirements by:
- Analyzing source code for cryptographic operations
- Scanning dependencies for non-compliant libraries
- Detecting prohibited or non-approved algorithms
- Verifying container base images and configurations
- Identifying operations that bypass RHEL's FIPS-certified cryptographic boundary

## Installation

After adding the marketplace (see [main README](../../README.md)), install this plugin:

```
/plugin install fips-compliance-checker@opendatahub-io/ai-helpers
```

## Prerequisites

The Python scanner uses Bandit in a containerized environment and requires one of the following container runtimes:

- **Podman** (recommended for RHEL/Fedora):
  ```bash
  dnf install podman
  ```

- **Docker**:
  ```bash
  # See https://docs.docker.com/get-docker/
  ```

On first run, the scanner will automatically pull the Bandit container image (`ghcr.io/pycqa/bandit/bandit:latest`, ~50MB).

**Air-gapped environments**: Pre-pull the image and ensure it's available in your local registry:
```bash
podman pull ghcr.io/pycqa/bandit/bandit:latest
# or
docker pull ghcr.io/pycqa/bandit/bandit:latest
```

## Usage

### Slash Command (Explicit)

Use the fully-qualified `/fips-compliance-checker:fips-scan` command for direct invocation:

```bash
# Scan the current project
/fips-compliance-checker:fips-scan

# Scan a specific container image
/fips-compliance-checker:fips-scan quay.io/myorg/myapp:v1.2.3
```

Note: Claude Code CLI currently requires the fully-qualified format `/plugin-name:command-name`.

### Natural Language (Auto-selection)

The agent will automatically activate when you ask FIPS-related questions:

- "Can you check if my app is FIPS compliant?"
- "I've added encryption to my authentication module. Is this FIPS compliant?"
- "We need to verify FIPS compliance before deploying to production"
- "Is using the standard Go crypto package okay for FIPS?"

The agent proactively activates when you mention:
- Cryptographic operations (encryption, hashing, TLS/SSL)
- FIPS, compliance, or security certifications
- Container images for Red Hat products or RHEL deployments
- Working with crypto libraries in Java, Python, Go, Rust, or C/C++

## What Gets Scanned

### Dependencies
- `requirements.txt`, `Pipfile` (Python)
- `go.mod`, `go.sum` (Go)
- `Cargo.toml`, `Cargo.lock` (Rust)
- `pom.xml`, `build.gradle` (Java)
- `package.json` (Node.js)
- `CMakeLists.txt`, `Makefile` (C/C++)

### Source Code Analysis
- Direct cryptographic operations
- Algorithm usage patterns
- Random number generation methods
- Key derivation functions
- JWT libraries and algorithm choices
- Certificate validation settings

### Container Analysis
- Base image compliance (UBI9, RHEL9, etc.)
- Installed cryptographic packages
- FIPS mode capability
- Static linking detection

### Build Configuration
- Static linking flags
- Vendored dependencies
- Compilation flags affecting FIPS
- Environment variables

## Default Exclusions

By default, the scanner excludes non-production code from analysis to focus on actual runtime compliance issues. The following patterns are automatically excluded:

### Test Code
- `*/tests/*` - Test directories
- `*/test_*.py` - Test file prefix pattern
- `*/*_test.py` - Test file suffix pattern
- `*/conftest.py` - pytest configuration

### Examples & Documentation
- `*/examples/*`, `*/samples/*` - Example code directories
- `*/demo/*`, `*/demos/*` - Demo applications
- `*/docs/examples/*` - Documentation examples
- `*/tutorials/*` - Tutorial code
- `*/playground/*` - Experimental/playground code

### Scripts & Utilities
- `*/benchmarks/*` - Benchmark code
- `*/scripts/*` - Utility scripts
- `*/tools/*` - Development tools
- `*/utilities/*` - Helper utilities

### Build Artifacts
- `*/venv/*`, `*/.venv/*`, `*/env/*` - Virtual environments
- `*/build/*`, `*/dist/*` - Build outputs
- `*/__pycache__/*`, `*/.eggs/*` - Python cache
- `*/node_modules/*` - Node.js dependencies

### Custom Exclusions

You can add additional exclusion patterns using the `--exclude` flag:

```bash
# Scan Python code with custom exclusions
cd fips-compliance-checker/scripts/python
./scan-python-fips.sh --exclude "*/vendor/*" --exclude "*/legacy/*"
```

**Note**: Custom exclusions are added to the default patterns (not replacing them).

## Compliance Report

The agent provides:

### Structured Findings
- **Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW
- **Categories**: Dependency, Source Code, Configuration, Container
- **Locations**: Exact file paths and line numbers
- **Detection Confidence**: High, Medium, Low

### Compliance Score
```
Dependency Compliance:    [X/40]
Source Code Compliance:   [X/30]
Configuration Compliance: [X/20]
Container Compliance:     [X/10]
─────────────────────────────────
Total Score:             [X/100]
```

### Remediation Guidance
- Specific action items (REPLACE, REMOVE, CONFIGURE, UPDATE)
- Priority levels (IMMEDIATE, HIGH, MEDIUM, LOW)
- Code examples (before/after)
- Verification commands

## Examples

### High-Risk Packages Detected

**Python:**
- `pycrypto`, `PyCryptodome` → CRITICAL (independent crypto)
- `hashlib.md5()` for security → HIGH
- `random` module for keys → HIGH

**Go:**
- Standard `crypto/*` without boringcrypto → CRITICAL
- `x/crypto` with ChaCha20, Curve25519 → CRITICAL

**Rust:**
- `ring`, `rust-crypto` → CRITICAL
- `openssl` not linked to system OpenSSL 3 → CRITICAL

**Java:**
- Bouncy Castle (non-FIPS provider) → CRITICAL
- JCA/JSSE without FIPS provider → HIGH

### Algorithm Compliance

**Prohibited:**
- MD5 (for security), SHA-1 (signatures) → HIGH/CRITICAL
- DES, 3DES, RC4, Blowfish → HIGH

**Non-Approved:**
- Blake3, ChaCha20, Curve25519 → CRITICAL

**Approved (if via FIPS module):**
- SHA-256, SHA-384, SHA-512, AES → PASS

## Agent Details

**Agent Name**: `fips-compliance-checker`
**Full Reference**: `fips-compliance-checker:fips-compliance-checker`
**Available Tools**: Glob, Grep, Read, WebFetch, TodoWrite, Bash, SlashCommand

## Further Reading

- [FIPS 140-3 Standard](https://csrc.nist.gov/publications/detail/fips/140/3/final)
- [RHEL 9 Security Hardening](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/security_hardening/index)
- [OpenSSL FIPS Provider](https://www.openssl.org/docs/man3.0/man7/fips_module.html)

## Contributing

See the main repository [CLAUDE.md](../../CLAUDE.md) for plugin development guidelines.
