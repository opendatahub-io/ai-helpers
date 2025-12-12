#!/bin/bash
# Layer 2: Bandit Integration for AST-Based FIPS Compliance Analysis
# Uses Bandit security linter to detect cryptographic issues

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the context analyzer
source "$SCRIPT_DIR/context-analyzer.sh"

# Bandit container image
BANDIT_IMAGE="ghcr.io/pycqa/bandit/bandit:latest"

# Detect available container runtime
detect_container_runtime() {
    if command -v podman &> /dev/null; then
        echo "podman"
        return 0
    elif command -v docker &> /dev/null; then
        echo "docker"
        return 0
    else
        return 1
    fi
}

# Check if container runtime is available
check_bandit_available() {
    local runtime
    if ! runtime=$(detect_container_runtime); then
        echo "ERROR: Container runtime (podman or docker) is required but not installed" >&2
        echo "" >&2
        echo "To install a container runtime:" >&2
        echo "  dnf install podman  # on RHEL/Fedora" >&2
        echo "  # or" >&2
        echo "  apt install podman  # on Debian/Ubuntu" >&2
        echo "  # or install Docker from https://docs.docker.com/get-docker/" >&2
        echo "" >&2
        echo "The Bandit scanner runs in a container using: $BANDIT_IMAGE" >&2
        echo "" >&2
        return 1
    fi

    # Store the runtime for use in other functions
    CONTAINER_RUNTIME="$runtime"
    return 0
}

# Run Bandit with crypto-focused filters
run_bandit_scan() {
    local target_path="$1"

    # Bandit test IDs for crypto-related issues:
    # B303 - MD5 usage
    # B304 - Insecure cipher usage
    # B305 - Insecure cipher modes
    # B311 - Random usage (pseudo-random)
    # B313 - XML bad cElementTree
    # B320 - XML bad lxml
    # B324 - hashlib usage
    # B501 - SSL/TLS insecure defaults
    # B502 - SSL bad defaults
    # B503 - SSL bad version
    # B504 - SSL insecure defaults
    # B505 - Weak cryptographic key
    # B506 - YAML load
    # B507 - SSH no host key verification

    # Build exclusion patterns
    # Start with basic exclusions that should always be present
    local exclude_patterns=()

    # Read exclusion patterns from environment variable if set
    if [ -n "${FIPS_EXCLUDE_PATTERNS:-}" ]; then
        # Convert space-separated patterns to array
        IFS=' ' read -ra exclude_patterns <<< "$FIPS_EXCLUDE_PATTERNS"
    fi

    # Convert patterns to Bandit's glob format (comma-separated with ** prefix)
    local bandit_exclude=""
    if [ ${#exclude_patterns[@]} -gt 0 ]; then
        # Join patterns with commas, ensuring they work with Bandit's glob syntax
        bandit_exclude=$(printf ",%s" "${exclude_patterns[@]}")
        bandit_exclude="${bandit_exclude:1}"  # Remove leading comma
    fi

    # Run Bandit in a container with the target path mounted
    # Use :Z for SELinux labeling on RHEL/Fedora systems
    local bandit_cmd=("$CONTAINER_RUNTIME" run --rm \
        -v "${target_path}:/scan:Z" \
        -w /scan \
        "$BANDIT_IMAGE" \
        -f json -r /scan \
        -t B303,B304,B305,B311,B324,B501,B502,B503,B504,B505)

    # Add exclusion patterns if any exist
    if [ -n "$bandit_exclude" ]; then
        bandit_cmd+=(--exclude "$bandit_exclude")
    fi

    local bandit_output
    bandit_output=$("${bandit_cmd[@]}" 2>/dev/null || true)

    echo "$bandit_output"
}

# Convert Bandit findings to our format with context metadata
convert_bandit_findings() {
    local bandit_json="$1"
    local target_path="$2"
    local findings=()

    # Parse Bandit results
    local results
    results=$(echo "$bandit_json" | jq -c '.results[]' 2>/dev/null || echo "")

    if [ -z "$results" ]; then
        echo "[]"
        return
    fi

    while IFS= read -r result; do
        # Extract fields from Bandit result
        local filename
        local line_number
        local test_id
        local test_name
        local issue_severity
        local issue_confidence
        local issue_text
        local code

        filename=$(echo "$result" | jq -r '.filename')
        line_number=$(echo "$result" | jq -r '.line_number')
        test_id=$(echo "$result" | jq -r '.test_id')
        test_name=$(echo "$result" | jq -r '.test_name')
        issue_severity=$(echo "$result" | jq -r '.issue_severity')
        issue_confidence=$(echo "$result" | jq -r '.issue_confidence')
        issue_text=$(echo "$result" | jq -r '.issue_text')
        code=$(echo "$result" | jq -r '.code')

        # Translate container path (/scan/...) back to host path
        # The container mounts target_path as /scan
        local host_filename
        host_filename="${filename#/scan}"
        if [ "$host_filename" = "$filename" ]; then
            # Path didn't start with /scan, use as-is
            host_filename="$filename"
        else
            # Prepend target_path
            host_filename="${target_path}${host_filename}"
        fi

        # Get relative path
        local rel_path
        rel_path=$(realpath --relative-to="$target_path" "$host_filename" 2>/dev/null || echo "$host_filename")

        # Get context metadata
        local context
        context=$(generate_context_json "$rel_path" "$line_number")

        # Map Bandit severity to our severity levels
        local our_severity="MEDIUM"
        case "$issue_severity" in
            "HIGH")
                our_severity="HIGH"
                ;;
            "MEDIUM")
                our_severity="MEDIUM"
                ;;
            "LOW")
                our_severity="LOW"
                ;;
        esac

        # Adjust severity based on test ID and context
        case "$test_id" in
            "B303") # MD5 usage
                # Check if in production code
                if echo "$context" | jq -r '.likely_production' | grep -q "true"; then
                    our_severity="HIGH"
                else
                    our_severity="MEDIUM"
                fi
                ;;
            "B304"|"B305") # Insecure cipher
                our_severity="CRITICAL"
                ;;
            "B311") # Random usage
                our_severity="HIGH"
                ;;
            "B505") # Weak cryptographic key
                our_severity="CRITICAL"
                ;;
        esac

        # Get remediation based on test ID
        local remediation
        remediation=$(get_remediation_for_test "$test_id" "$test_name")

        # Create finding in our format
        local finding
        finding=$(cat <<EOF
{
  "id": "BANDIT-$test_id-$(echo "$filename:$line_number" | md5sum | cut -c1-8)",
  "severity": "$our_severity",
  "category": "SOURCE_CODE",
  "status": "FAIL",
  "location": {
    "file": "$rel_path",
    "line": $line_number,
    "code_snippet": $(echo "$code" | jq -R -s '.')
  },
  "detection": {
    "type": "ALGORITHM",
    "name": "$test_name",
    "bandit_test_id": "$test_id",
    "confidence": "$issue_confidence"
  },
  "compliance": {
    "violation": $(echo "$issue_text" | jq -R -s '.'),
    "fips_section": "140-3:7.5.1",
    "rhel_requirement": "Must use FIPS-approved cryptographic algorithms and methods",
    "risk_profile": "ALGORITHM_COMPLIANCE"
  },
  "context": $context,
  "remediation": $remediation
}
EOF
)
        findings+=("$finding")
    done <<< "$results"

    # Output findings as JSON array
    if [ ${#findings[@]} -gt 0 ]; then
        printf '%s\n' "${findings[@]}" | jq -s '.'
    else
        echo "[]"
    fi
}

# Get remediation advice for specific Bandit test
get_remediation_for_test() {
    local test_id="$1"
    local test_name="$2"

    case "$test_id" in
        "B303")
            cat <<'EOF'
{
  "action": "REPLACE",
  "priority": "HIGH",
  "effort": "LOW",
  "recommendation": "Replace MD5 with SHA-256 or higher. If MD5 is used for non-security purposes (checksums), add usedforsecurity=False parameter.",
  "code_example": {
    "before": "hashlib.md5(data)",
    "after": "hashlib.sha256(data)  # or hashlib.md5(data, usedforsecurity=False) for checksums"
  },
  "verification_command": "grep -r 'hashlib.md5' --include='*.py' ."
}
EOF
            ;;
        "B304"|"B305")
            cat <<'EOF'
{
  "action": "REPLACE",
  "priority": "IMMEDIATE",
  "effort": "MEDIUM",
  "recommendation": "Replace insecure cipher with FIPS-approved AES-GCM or AES-CBC with HMAC",
  "code_example": {
    "before": "Crypto.Cipher.DES.new(key, mode)",
    "after": "from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes; Cipher(algorithms.AES(key), modes.GCM(nonce))"
  },
  "verification_command": "bandit -t B304,B305 -r ."
}
EOF
            ;;
        "B311")
            cat <<'EOF'
{
  "action": "REPLACE",
  "priority": "HIGH",
  "effort": "LOW",
  "recommendation": "Replace random module with secrets module for cryptographic purposes",
  "code_example": {
    "before": "import random; token = random.randint(0, 1000000)",
    "after": "import secrets; token = secrets.randbelow(1000001)"
  },
  "verification_command": "grep -r 'import random' --include='*.py' . | grep -v SystemRandom"
}
EOF
            ;;
        "B324")
            cat <<'EOF'
{
  "action": "CONFIGURE",
  "priority": "MEDIUM",
  "effort": "LOW",
  "recommendation": "Ensure hashlib is using FIPS-approved algorithms (SHA-256+). If using weak algorithms, replace them.",
  "code_example": {
    "before": "hashlib.new('md5')",
    "after": "hashlib.sha256()"
  },
  "verification_command": "bandit -t B324 -r ."
}
EOF
            ;;
        "B501"|"B502"|"B503"|"B504")
            cat <<'EOF'
{
  "action": "CONFIGURE",
  "priority": "HIGH",
  "effort": "MEDIUM",
  "recommendation": "Configure SSL/TLS to use only secure protocols (TLS 1.2+) and FIPS-approved cipher suites",
  "code_example": {
    "before": "ssl.wrap_socket(sock)",
    "after": "context = ssl.create_default_context(); context.minimum_version = ssl.TLSVersion.TLSv1_2; context.wrap_socket(sock)"
  },
  "verification_command": "bandit -t B501,B502,B503,B504 -r ."
}
EOF
            ;;
        "B505")
            cat <<'EOF'
{
  "action": "REPLACE",
  "priority": "IMMEDIATE",
  "effort": "LOW",
  "recommendation": "Use stronger cryptographic key (minimum 2048-bit for RSA, 256-bit for ECC)",
  "code_example": {
    "before": "key = RSA.generate(1024)",
    "after": "from cryptography.hazmat.primitives.asymmetric import rsa; key = rsa.generate_private_key(public_exponent=65537, key_size=2048)"
  },
  "verification_command": "bandit -t B505 -r ."
}
EOF
            ;;
        *)
            cat <<EOF
{
  "action": "REVIEW",
  "priority": "MEDIUM",
  "effort": "MEDIUM",
  "recommendation": "Review and remediate: $test_name",
  "verification_command": "bandit -t $test_id -r ."
}
EOF
            ;;
    esac
}

# Main function
main() {
    local target_path="${1:-.}"

    # Ensure target path is absolute
    target_path=$(realpath "$target_path")

    echo "# Checking if container runtime is available..." >&2
    if ! check_bandit_available; then
        # Return error JSON
        cat <<EOF
{
  "error": "Container runtime (podman or docker) not available",
  "findings": [],
  "container_runtime_required": true,
  "bandit_image": "$BANDIT_IMAGE"
}
EOF
        return 1
    fi

    echo "# Using container runtime: $CONTAINER_RUNTIME" >&2

    echo "# Running Bandit security scan..." >&2
    local bandit_output
    bandit_output=$(run_bandit_scan "$target_path")

    echo "# Processing Bandit results..." >&2
    local findings
    findings=$(convert_bandit_findings "$bandit_output" "$target_path")

    # Get Bandit version from container
    local bandit_version
    bandit_version=$("$CONTAINER_RUNTIME" run --rm "$BANDIT_IMAGE" --version 2>&1 | head -n1 || echo 'unknown')

    # Output results
    cat <<EOF
{
  "bandit_version": "$bandit_version",
  "findings": $findings
}
EOF
}

# If sourced, don't run main
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
