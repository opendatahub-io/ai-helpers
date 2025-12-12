#!/bin/bash
# FIPS 140-3 Python Compliance Scanner
# Main orchestrator coordinating all scanning layers

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# Default options
TARGET_PATH="."
OUTPUT_JSON=true
EXCLUDE_PATTERNS=()
CONFIG_FILE=""

# Default exclusion patterns for non-production code
# These patterns filter out test, example, and utility code that shouldn't be scanned
DEFAULT_EXCLUDE_PATTERNS=(
    # Test patterns
    "*/tests/*"
    "*/test_*.py"
    "*/*_test.py"
    "*/conftest.py"
    # Example/demo patterns
    "*/examples/*"
    "*/samples/*"
    "*/demo/*"
    "*/demos/*"
    "*/docs/examples/*"
    "*/tutorials/*"
    "*/playground/*"
    # Script/utility patterns
    "*/benchmarks/*"
    "*/scripts/*"
    "*/tools/*"
    "*/utilities/*"
    # Build/environment patterns (always excluded)
    "*/venv/*"
    "*/.venv/*"
    "*/env/*"
    "*/build/*"
    "*/dist/*"
    "*/__pycache__/*"
    "*/.eggs/*"
    "*/node_modules/*"
)

# Usage information
usage() {
    cat <<EOF
FIPS 140-3 Python Compliance Scanner

Usage: $(basename "$0") [OPTIONS]

Options:
  --path PATH          Target directory to scan (default: current directory)
  --json               Output results as JSON (default: true)
  --text               Output results as human-readable text
  --exclude PATTERN    Exclude files matching pattern (can be used multiple times)
  --config FILE        Load configuration from YAML file
  --help               Show this help message

Examples:
  # Scan current directory
  $(basename "$0")

  # Scan specific directory
  $(basename "$0") --path /path/to/project

  # Scan and exclude tests
  $(basename "$0") --exclude 'tests/**' --exclude 'examples/**'

  # Use configuration file
  $(basename "$0") --config .fips-compliance.yaml

Exit Codes:
  0 - No violations found
  1 - CRITICAL violations found
  2 - HIGH violations found
  3 - MEDIUM violations found
  4 - Script error

EOF
    exit 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --path)
                TARGET_PATH="$2"
                shift 2
                ;;
            --json)
                OUTPUT_JSON=true
                shift
                ;;
            --text)
                OUTPUT_JSON=false
                shift
                ;;
            --exclude)
                EXCLUDE_PATTERNS+=("$2")
                shift 2
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --help|-h)
                usage
                ;;
            *)
                echo "Unknown option: $1" >&2
                usage
                ;;
        esac
    done
}

# Combine default and user-provided exclusion patterns
get_all_exclusions() {
    local combined=("${DEFAULT_EXCLUDE_PATTERNS[@]}")

    # Add user-provided patterns
    if [ ${#EXCLUDE_PATTERNS[@]} -gt 0 ]; then
        combined+=("${EXCLUDE_PATTERNS[@]}")
    fi

    printf '%s\n' "${combined[@]}"
}

# Convert exclusion patterns to find command format
get_find_exclusions() {
    local patterns=("$@")
    local find_args=()

    for pattern in "${patterns[@]}"; do
        find_args+=("-not" "-path" "$pattern")
    done

    printf '%s\n' "${find_args[@]}"
}

# Calculate summary statistics from findings
calculate_summary() {
    local all_findings="$1"

    local total
    local critical
    local high
    local medium
    local low
    local production_critical

    total=$(echo "$all_findings" | jq 'length')
    critical=$(echo "$all_findings" | jq '[.[] | select(.severity == "CRITICAL")] | length')
    high=$(echo "$all_findings" | jq '[.[] | select(.severity == "HIGH")] | length')
    medium=$(echo "$all_findings" | jq '[.[] | select(.severity == "MEDIUM")] | length')
    low=$(echo "$all_findings" | jq '[.[] | select(.severity == "LOW")] | length')
    production_critical=$(echo "$all_findings" | jq '[.[] | select(.context.likely_production == true and (.severity == "CRITICAL" or .severity == "HIGH"))] | length')

    cat <<EOF
{
  "total_findings": $total,
  "critical": $critical,
  "high": $high,
  "medium": $medium,
  "low": $low,
  "production_critical": $production_critical
}
EOF
}

# Determine overall compliance status
# Returns exit code only (no output to avoid script termination with set -e)
determine_status() {
    local summary="$1"

    local critical
    local high

    critical=$(echo "$summary" | jq -r '.critical')
    high=$(echo "$summary" | jq -r '.high')

    if [ "$critical" -gt 0 ]; then
        return 1
    elif [ "$high" -gt 0 ]; then
        return 2
    else
        return 0
    fi
}

# Calculate exit code based on findings
calculate_exit_code() {
    local summary="$1"

    local critical
    local high
    local medium

    critical=$(echo "$summary" | jq -r '.critical')
    high=$(echo "$summary" | jq -r '.high')
    medium=$(echo "$summary" | jq -r '.medium')

    if [ "$critical" -gt 0 ]; then
        return 1
    elif [ "$high" -gt 0 ]; then
        return 2
    elif [ "$medium" -gt 0 ]; then
        return 3
    else
        return 0
    fi
}

# Main scanning function
main() {
    parse_args "$@"

    # Ensure target path exists and is absolute
    if [ ! -d "$TARGET_PATH" ]; then
        echo "ERROR: Target path does not exist: $TARGET_PATH" >&2
        exit 4
    fi
    TARGET_PATH=$(realpath "$TARGET_PATH")

    # Export exclusion patterns for subscripts
    local all_exclusions
    mapfile -t all_exclusions < <(get_all_exclusions)
    export FIPS_EXCLUDE_PATTERNS="${all_exclusions[*]}"

    # Start timing
    local start_time
    start_time=$(date +%s)

    # Show progress if not in JSON mode
    if [ "$OUTPUT_JSON" != "true" ]; then
        echo "═══════════════════════════════════════════════"
        echo " FIPS 140-3 Python Compliance Scanner"
        echo "═══════════════════════════════════════════════"
        echo ""
        echo "Target: $TARGET_PATH"
        echo ""
    fi

    # Phase 1: Dependency Analysis
    if [ "$OUTPUT_JSON" != "true" ]; then
        echo "Phase 1/3: Dependency Analysis..."
    fi
    local dep_findings
    dep_findings=$("$LIB_DIR/check-dependencies.sh" "$TARGET_PATH" 2>/dev/null || echo "[]")

    # Phase 2: Bandit/AST Analysis
    if [ "$OUTPUT_JSON" != "true" ]; then
        echo "Phase 2/3: Source Code Analysis (Bandit)..."
    fi
    local bandit_result
    bandit_result=$("$LIB_DIR/analyze-source.sh" "$TARGET_PATH" 2>/dev/null || echo '{"findings": []}')
    local bandit_findings
    bandit_findings=$(echo "$bandit_result" | jq -r '.findings // []')

    # Phase 3: Pattern Matching
    if [ "$OUTPUT_JSON" != "true" ]; then
        echo "Phase 3/3: Pattern-Based Detection..."
    fi
    local pattern_findings
    pattern_findings=$("$LIB_DIR/check-patterns.sh" "$TARGET_PATH" 2>/dev/null || echo "[]")

    # Combine all findings
    local all_findings
    all_findings=$(jq -s 'add' <(echo "$dep_findings") <(echo "$bandit_findings") <(echo "$pattern_findings"))

    # Calculate statistics
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    local summary
    summary=$(calculate_summary "$all_findings")

    local overall_status
    determine_status "$summary" || overall_status=$?
    overall_status=${overall_status:-0}

    local status_text
    case $overall_status in
        0) status_text="PASS" ;;
        1) status_text="FAIL" ;;
        2) status_text="FAIL" ;;
        *) status_text="NEEDS_REVIEW" ;;
    esac

    # Count files scanned (approximate)
    local files_scanned
    local all_exclusions
    mapfile -t all_exclusions < <(get_all_exclusions)

    # Build find command with exclusions
    local find_cmd=("find" "$TARGET_PATH" "-name" "*.py" "-type" "f")
    for pattern in "${all_exclusions[@]}"; do
        find_cmd+=("-not" "-path" "$pattern")
    done

    files_scanned=$("${find_cmd[@]}" 2>/dev/null | wc -l)

    # Output results
    if [ "$OUTPUT_JSON" == "true" ]; then
        # JSON output
        cat <<EOF
{
  "metadata": {
    "scan_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "scan_duration_seconds": $duration,
    "scanner_version": "1.0.0",
    "target_path": "$TARGET_PATH",
    "files_scanned": $files_scanned
  },
  "summary": $summary,
  "overall_status": "$status_text",
  "findings": $all_findings
}
EOF
    else
        # Text output
        echo ""
        echo "═══════════════════════════════════════════════"
        echo " Scan Complete"
        echo "═══════════════════════════════════════════════"
        echo ""
        echo "Overall Status: $status_text"
        echo "Scan Duration: ${duration}s"
        echo "Files Scanned: $files_scanned"
        echo ""
        echo "Summary:"
        echo "  Total Findings:        $(echo "$summary" | jq -r '.total_findings')"
        echo "  Critical:              $(echo "$summary" | jq -r '.critical')"
        echo "  High:                  $(echo "$summary" | jq -r '.high')"
        echo "  Medium:                $(echo "$summary" | jq -r '.medium')"
        echo "  Low:                   $(echo "$summary" | jq -r '.low')"
        echo "  Production Critical:   $(echo "$summary" | jq -r '.production_critical')"
        echo ""

        if [ "$(echo "$summary" | jq -r '.total_findings')" -gt 0 ]; then
            echo "Findings:"
            echo "$all_findings" | jq -r '.[] | "  [\(.severity)] \(.location.file):\(.location.line // "N/A") - \(.compliance.violation)"'
            echo ""
        fi

        echo "For detailed findings, run with --json flag and pipe to jq"
        echo ""
    fi

    # Calculate and return exit code
    calculate_exit_code "$summary"
    return $?
}

# Run main function
main "$@"
