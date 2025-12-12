#!/bin/bash
# Layer 1: Dependency Analysis for FIPS Compliance
# Scans Python dependency manifests for prohibited packages

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATTERNS_DIR="$(cd "$SCRIPT_DIR/../patterns" && pwd)"
PROHIBITED_PACKAGES_FILE="$PATTERNS_DIR/prohibited-packages.txt"

# Source the context analyzer
source "$SCRIPT_DIR/context-analyzer.sh"

# Load prohibited packages into array
load_prohibited_packages() {
    mapfile -t PROHIBITED_PACKAGES < <(grep -v '^\s*#' "$PROHIBITED_PACKAGES_FILE" | grep -v '^\s*$' || true)
}

# Check a single dependency manifest file
# Args: file_path, target_path (base directory for relative paths)
# Outputs: JSON array of findings
check_dependency_file() {
    local file_path="$1"
    local target_path="$2"
    local findings=()

    # Get relative path for cleaner output
    local rel_path
    rel_path=$(realpath --relative-to="$target_path" "$file_path" 2>/dev/null || echo "$file_path")

    # Get context metadata
    local is_dev_dep
    is_dev_dep=$(is_dev_dependency_file "$rel_path" && echo "true" || echo "false")

    # Read file line by line
    local line_num=0
    while IFS= read -r line || [ -n "$line" ]; do
        ((line_num++))

        # Skip comments and empty lines
        [[ "$line" =~ ^\s*# ]] && continue
        [[ -z "${line// }" ]] && continue

        # Extract package name (handle various formats)
        local package_name
        package_name=$(echo "$line" | sed -E 's/([a-zA-Z0-9_-]+).*/\1/' | tr '[:upper:]' '[:lower:]')

        # Check if package is prohibited
        for prohibited_pkg in "${PROHIBITED_PACKAGES[@]}"; do
            prohibited_pkg=$(echo "$prohibited_pkg" | tr '[:upper:]' '[:lower:]')

            if [[ "$package_name" == "$prohibited_pkg" ]]; then
                # Determine severity
                local severity="CRITICAL"
                local reason="Non-FIPS approved cryptographic package"

                # Check if it's a high-risk package that requires inspection
                if [[ "$prohibited_pkg" =~ ^(pyjwt|python-jose|jose|authlib)$ ]]; then
                    severity="HIGH"
                    reason="JWT library that may use non-compliant crypto (requires inspection)"
                fi

                # Generate context
                local context
                context=$(generate_context_json "$rel_path" "$line_num")

                # Create finding JSON
                local finding
                finding=$(cat <<EOF
{
  "id": "DEP-$(printf '%03d' ${#findings[@]})",
  "severity": "$severity",
  "category": "DEPENDENCY",
  "status": "FAIL",
  "location": {
    "file": "$rel_path",
    "line": $line_num,
    "package": "$package_name",
    "raw_line": "$(echo "$line" | sed 's/"/\\"/g')"
  },
  "detection": {
    "type": "PROHIBITED_PACKAGE",
    "name": "$package_name",
    "confidence": "HIGH"
  },
  "compliance": {
    "violation": "$reason",
    "fips_section": "140-3:7.5.1",
    "rhel_requirement": "Must use system-provided FIPS cryptographic module",
    "risk_profile": "CRYPTOGRAPHIC_BOUNDARY"
  },
  "context": $context,
  "remediation": {
    "action": "REMOVE",
    "priority": "IMMEDIATE",
    "effort": "MEDIUM",
    "recommendation": "Remove '$package_name' and use FIPS-compliant alternatives",
    "alternatives": $(get_alternatives "$package_name")
  }
}
EOF
)
                findings+=("$finding")
            fi
        done
    done < "$file_path"

    # Output findings as JSON array
    if [ ${#findings[@]} -gt 0 ]; then
        printf '%s\n' "${findings[@]}" | jq -s '.'
    else
        echo "[]"
    fi
}

# Get alternative packages for a prohibited package
get_alternatives() {
    local package_name="$1"

    case "$package_name" in
        pycrypto|pycryptodome|pycryptodomex)
            echo '["cryptography>=41.0.0 (must link to system OpenSSL)"]'
            ;;
        blake3|xxhash|mmh3)
            echo '["hashlib with SHA-256 or SHA-512"]'
            ;;
        argon2-cffi|argon2pure)
            echo '["PBKDF2 via cryptography.hazmat.primitives.kdf.pbkdf2"]'
            ;;
        bcrypt|scrypt|py-scrypt)
            echo '["PBKDF2 via cryptography.hazmat.primitives.kdf.pbkdf2"]'
            ;;
        pyopenssl)
            echo '["ssl module (built-in)", "cryptography library"]'
            ;;
        pyjwt|python-jose|jose)
            echo '["Review JWT algorithm configuration, ensure HS256/RS256 only"]'
            ;;
        *)
            echo '["cryptography>=41.0.0 (system-linked)"]'
            ;;
    esac
}

# Main function
main() {
    local target_path="${1:-.}"
    local all_findings=()

    # Ensure target path is absolute
    target_path=$(realpath "$target_path")

    # Load prohibited packages
    load_prohibited_packages

    # Find all dependency manifest files
    local manifest_files=()
    while IFS= read -r -d $'\0' file; do
        manifest_files+=("$file")
    done < <(find "$target_path" -type f \( \
        -name "requirements*.txt" -o \
        -name "Pipfile" -o \
        -name "Pipfile.lock" -o \
        -name "setup.py" -o \
        -name "setup.cfg" -o \
        -name "pyproject.toml" -o \
        -name "poetry.lock" \
    \) -not -path "*/venv/*" \
      -not -path "*/.venv/*" \
      -not -path "*/env/*" \
      -not -path "*/__pycache__/*" \
      -not -path "*/build/*" \
      -not -path "*/dist/*" \
      -print0 2>/dev/null)

    # Check each manifest file
    for manifest_file in "${manifest_files[@]}"; do
        local findings
        findings=$(check_dependency_file "$manifest_file" "$target_path")

        if [ "$findings" != "[]" ]; then
            all_findings+=("$findings")
        fi
    done

    # Combine all findings
    if [ ${#all_findings[@]} -gt 0 ]; then
        # Merge all JSON arrays
        printf '%s\n' "${all_findings[@]}" | jq -s 'add'
    else
        echo "[]"
    fi
}

# If sourced, don't run main
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
