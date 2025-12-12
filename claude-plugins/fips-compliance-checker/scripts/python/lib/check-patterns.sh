#!/bin/bash
# Layer 3: Pattern-Based Detection for FIPS Compliance
# Detects crypto usage patterns that Bandit might miss

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATTERNS_DIR="$(cd "$SCRIPT_DIR/../patterns" && pwd)"

# Source the context analyzer
source "$SCRIPT_DIR/context-analyzer.sh"

# Build find command with exclusion patterns
# Returns a list of Python files that match inclusion criteria and don't match exclusion patterns
find_python_files() {
    local target_path="$1"
    local find_cmd=("find" "$target_path" "-name" "*.py" "-type" "f")

    # Add exclusion patterns from environment variable if set
    if [ -n "${FIPS_EXCLUDE_PATTERNS:-}" ]; then
        # Convert space-separated patterns to array
        local exclude_patterns
        IFS=' ' read -ra exclude_patterns <<< "$FIPS_EXCLUDE_PATTERNS"

        # Add each pattern as a -not -path filter
        for pattern in "${exclude_patterns[@]}"; do
            find_cmd+=("-not" "-path" "$pattern")
        done
    fi

    # Execute find command
    "${find_cmd[@]}" 2>/dev/null || true
}

# Search for MD5 usage
check_md5_usage() {
    local target_path="$1"
    local findings=()

    # Search for hashlib.md5() usage
    while IFS=: read -r file line content; do
        # Check for usedforsecurity=False (allowed use case)
        local false_positive=false
        local adjusted_severity="HIGH"

        if echo "$content" | grep -q "usedforsecurity\s*=\s*False"; then
            false_positive=true
            adjusted_severity="LOW"
        fi

        # Get relative path
        local rel_path
        rel_path=$(realpath --relative-to="$target_path" "$file" 2>/dev/null || echo "$file")

        # Get context
        local context
        context=$(generate_context_json "$rel_path" "$line")

        # Create finding
        local finding
        finding=$(cat <<EOF
{
  "id": "PATTERN-MD5-$(echo "$file:$line" | md5sum | cut -c1-8)",
  "severity": "$adjusted_severity",
  "category": "SOURCE_CODE",
  "status": "$([ "$false_positive" == "true" ] && echo "WARNING" || echo "FAIL")",
  "location": {
    "file": "$rel_path",
    "line": $line,
    "code_snippet": "$(echo "$content" | sed 's/"/\\"/g' | sed 's/\t/  /g')"
  },
  "detection": {
    "type": "ALGORITHM",
    "name": "MD5",
    "confidence": "HIGH"
  },
  "compliance": {
    "violation": "MD5 hash algorithm usage",
    "fips_section": "140-3:Annex A",
    "rhel_requirement": "MD5 not approved for security purposes",
    "risk_profile": "ALGORITHM_COMPLIANCE"
  },
  "context": $context,
  "false_positive_check": {
    "is_security_context": $([ "$false_positive" == "false" ] && echo "true" || echo "false"),
    "has_mitigation": $false_positive,
    "mitigation_details": "$([ "$false_positive" == "true" ] && echo "usedforsecurity=False flag present" || echo "none")"
  },
  "remediation": {
    "action": "REPLACE",
    "priority": "$([ "$false_positive" == "true" ] && echo "LOW" || echo "HIGH")",
    "effort": "LOW",
    "recommendation": "$([ "$false_positive" == "true" ] && echo "MD5 marked as non-security use - acceptable for checksums" || echo "Replace MD5 with SHA-256 or higher")",
    "code_example": {
      "before": "hashlib.md5(data).hexdigest()",
      "after": "hashlib.sha256(data).hexdigest()"
    }
  }
}
EOF
)
        findings+=("$finding")
    done < <(find_python_files "$target_path" | \
        xargs -r grep -n "hashlib\.md5\|from hashlib import md5\|import md5" 2>/dev/null | \
        grep -v "^\s*#" || true)

    printf '%s\n' "${findings[@]}"
}

# Search for SHA-1 usage (deprecated for signatures)
check_sha1_usage() {
    local target_path="$1"
    local findings=()

    while IFS=: read -r file line content; do
        # Check for usedforsecurity=False
        local false_positive=false
        local adjusted_severity="HIGH"

        if echo "$content" | grep -q "usedforsecurity\s*=\s*False"; then
            false_positive=true
            adjusted_severity="LOW"
        fi

        # Get relative path
        local rel_path
        rel_path=$(realpath --relative-to="$target_path" "$file" 2>/dev/null || echo "$file")

        # Get context
        local context
        context=$(generate_context_json "$rel_path" "$line")

        # Create finding
        local finding
        finding=$(cat <<EOF
{
  "id": "PATTERN-SHA1-$(echo "$file:$line" | md5sum | cut -c1-8)",
  "severity": "$adjusted_severity",
  "category": "SOURCE_CODE",
  "status": "$([ "$false_positive" == "true" ] && echo "WARNING" || echo "FAIL")",
  "location": {
    "file": "$rel_path",
    "line": $line,
    "code_snippet": "$(echo "$content" | sed 's/"/\\"/g' | sed 's/\t/  /g')"
  },
  "detection": {
    "type": "ALGORITHM",
    "name": "SHA-1",
    "confidence": "HIGH"
  },
  "compliance": {
    "violation": "SHA-1 hash algorithm usage (deprecated for signatures)",
    "fips_section": "140-3:Annex A",
    "rhel_requirement": "SHA-1 deprecated for digital signatures and MACs",
    "risk_profile": "ALGORITHM_COMPLIANCE"
  },
  "context": $context,
  "false_positive_check": {
    "is_security_context": $([ "$false_positive" == "false" ] && echo "true" || echo "false"),
    "has_mitigation": $false_positive,
    "mitigation_details": "$([ "$false_positive" == "true" ] && echo "usedforsecurity=False flag present" || echo "none")"
  },
  "remediation": {
    "action": "REPLACE",
    "priority": "MEDIUM",
    "effort": "LOW",
    "recommendation": "Replace SHA-1 with SHA-256 or higher for new applications",
    "code_example": {
      "before": "hashlib.sha1(data).hexdigest()",
      "after": "hashlib.sha256(data).hexdigest()"
    }
  }
}
EOF
)
        findings+=("$finding")
    done < <(find_python_files "$target_path" | \
        xargs -r grep -n "hashlib\.sha1\|from hashlib import sha1" 2>/dev/null | \
        grep -v "^\s*#" || true)

    printf '%s\n' "${findings[@]}"
}

# Search for random module usage (non-cryptographic)
check_random_module() {
    local target_path="$1"
    local findings=()

    while IFS=: read -r file line content; do
        # Skip if it's importing SystemRandom (which is OK)
        if echo "$content" | grep -q "SystemRandom"; then
            continue
        fi

        # Get relative path
        local rel_path
        rel_path=$(realpath --relative-to="$target_path" "$file" 2>/dev/null || echo "$file")

        # Get context
        local context
        context=$(generate_context_json "$rel_path" "$line")

        # Check if likely used for crypto (heuristic)
        local severity="MEDIUM"
        if echo "$content" | grep -qE "(key|token|password|secret|nonce|salt|iv)"; then
            severity="HIGH"
        fi

        # Create finding
        local finding
        finding=$(cat <<EOF
{
  "id": "PATTERN-RANDOM-$(echo "$file:$line" | md5sum | cut -c1-8)",
  "severity": "$severity",
  "category": "SOURCE_CODE",
  "status": "WARNING",
  "location": {
    "file": "$rel_path",
    "line": $line,
    "code_snippet": "$(echo "$content" | sed 's/"/\\"/g' | sed 's/\t/  /g')"
  },
  "detection": {
    "type": "RNG",
    "name": "random_module",
    "confidence": "MEDIUM"
  },
  "compliance": {
    "violation": "Non-cryptographic random number generator",
    "fips_section": "140-3:7.9",
    "rhel_requirement": "Must use cryptographically secure RNG for security purposes",
    "risk_profile": "ALGORITHM_COMPLIANCE"
  },
  "context": $context,
  "remediation": {
    "action": "REPLACE",
    "priority": "$([ "$severity" == "HIGH" ] && echo "HIGH" || echo "MEDIUM")",
    "effort": "LOW",
    "recommendation": "Replace random module with secrets module for cryptographic purposes",
    "code_example": {
      "before": "import random; key = random.randint(0, 255)",
      "after": "import secrets; key = secrets.randbelow(256)"
    }
  }
}
EOF
)
        findings+=("$finding")
    done < <(find_python_files "$target_path" | \
        xargs -r grep -n "^import random\|^from random import" 2>/dev/null | \
        grep -v "SystemRandom" | grep -v "^\s*#" || true)

    printf '%s\n' "${findings[@]}"
}

# Search for prohibited crypto library imports
check_prohibited_imports() {
    local target_path="$1"
    local findings=()

    # Load prohibited import patterns
    local patterns
    patterns=$(grep -v '^\s*#' "$PATTERNS_DIR/prohibited-imports.txt" | grep -v '^\s*$' || true)

    while IFS= read -r pattern; do
        while IFS=: read -r file line content; do
            # Get relative path
            local rel_path
            rel_path=$(realpath --relative-to="$target_path" "$file" 2>/dev/null || echo "$file")

            # Get context
            local context
            context=$(generate_context_json "$rel_path" "$line")

            # Determine severity based on pattern
            local severity="CRITICAL"
            local lib_name
            lib_name=$(echo "$pattern" | sed -E 's/^(import|from) ([^ ]+).*/\2/')

            if echo "$lib_name" | grep -qE "^random"; then
                severity="HIGH"
            fi

            # Create finding
            local finding
            finding=$(cat <<EOF
{
  "id": "PATTERN-IMPORT-$(echo "$file:$line:$pattern" | md5sum | cut -c1-8)",
  "severity": "$severity",
  "category": "SOURCE_CODE",
  "status": "FAIL",
  "location": {
    "file": "$rel_path",
    "line": $line,
    "code_snippet": "$(echo "$content" | sed 's/"/\\"/g' | sed 's/\t/  /g')"
  },
  "detection": {
    "type": "LIBRARY",
    "name": "$lib_name",
    "pattern": "$(echo "$pattern" | sed 's/"/\\"/g')",
    "confidence": "HIGH"
  },
  "compliance": {
    "violation": "Prohibited cryptographic library import",
    "fips_section": "140-3:7.5.1",
    "rhel_requirement": "Must not use non-FIPS approved cryptographic libraries",
    "risk_profile": "CRYPTOGRAPHIC_BOUNDARY"
  },
  "context": $context,
  "remediation": {
    "action": "REPLACE",
    "priority": "IMMEDIATE",
    "effort": "MEDIUM",
    "recommendation": "Remove prohibited import and use FIPS-compliant alternatives",
    "alternatives": ["cryptography library (system-linked)", "hashlib (approved algorithms only)"]
  }
}
EOF
)
            findings+=("$finding")
        done < <(find_python_files "$target_path" | \
            xargs -r grep -n "$pattern" 2>/dev/null | grep -v "^\s*#" || true)
    done <<< "$patterns"

    printf '%s\n' "${findings[@]}"
}

# Main function
main() {
    local target_path="${1:-.}"
    local all_findings=()

    # Ensure target path is absolute
    target_path=$(realpath "$target_path")

    echo "# Checking MD5 usage..." >&2
    while IFS= read -r finding; do
        [ -n "$finding" ] && all_findings+=("$finding")
    done < <(check_md5_usage "$target_path")

    echo "# Checking SHA-1 usage..." >&2
    while IFS= read -r finding; do
        [ -n "$finding" ] && all_findings+=("$finding")
    done < <(check_sha1_usage "$target_path")

    echo "# Checking random module usage..." >&2
    while IFS= read -r finding; do
        [ -n "$finding" ] && all_findings+=("$finding")
    done < <(check_random_module "$target_path")

    echo "# Checking prohibited imports..." >&2
    while IFS= read -r finding; do
        [ -n "$finding" ] && all_findings+=("$finding")
    done < <(check_prohibited_imports "$target_path")

    # Output all findings as JSON array
    if [ ${#all_findings[@]} -gt 0 ]; then
        printf '%s\n' "${all_findings[@]}" | jq -s '.'
    else
        echo "[]"
    fi
}

# If sourced, don't run main
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
