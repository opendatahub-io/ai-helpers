#!/bin/bash
# Integration tests for Python FIPS compliance scanner

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCANNER="$SCRIPT_DIR/../scripts/python/scan-python-fips.sh"
FIXTURES_DIR="$SCRIPT_DIR/fixtures/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Print test result
print_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [ "$result" == "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        echo -e "  ${RED}$message${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test 1: Scanner script exists and is executable
test_scanner_exists() {
    local test_name="Scanner script exists and is executable"

    if [ -x "$SCANNER" ]; then
        print_result "$test_name" "PASS" ""
    else
        print_result "$test_name" "FAIL" "Scanner script not found or not executable: $SCANNER"
    fi
}

# Test 2: Violating project scan detects violations
test_violating_project() {
    local test_name="Violating project scan detects violations"
    local violations_found=false

    if [ ! -d "$FIXTURES_DIR/violating_project" ]; then
        print_result "$test_name" "FAIL" "Violating project fixture not found"
        return
    fi

    # Run scanner on violating project
    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/violating_project" --json 2>/dev/null || true)

    # Check if violations were found
    local total_findings
    total_findings=$(echo "$output" | jq -r '.summary.total_findings // 0')

    if [ "$total_findings" -gt 0 ]; then
        violations_found=true
    fi

    if $violations_found; then
        print_result "$test_name" "PASS" ""
        echo "  Found $total_findings violation(s)"
    else
        print_result "$test_name" "FAIL" "Expected violations but found none"
    fi
}

# Test 3: Violating project has pycryptodome dependency violation
test_pycryptodome_detection() {
    local test_name="Detects pycryptodome in dependencies"

    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/violating_project" --json 2>/dev/null || true)

    local pycryptodome_found
    pycryptodome_found=$(echo "$output" | jq -r '[.findings[] | select(.category == "DEPENDENCY" and (.detection.name | contains("pycryptodome")))] | length')

    if [ "$pycryptodome_found" -gt 0 ]; then
        print_result "$test_name" "PASS" ""
    else
        print_result "$test_name" "FAIL" "pycryptodome dependency violation not detected"
    fi
}

# Test 4: Violating project has MD5 usage violations
test_md5_detection() {
    local test_name="Detects MD5 usage in source code"

    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/violating_project" --json 2>/dev/null || true)

    local md5_found
    md5_found=$(echo "$output" | jq -r '[.findings[] | select(.detection.name | contains("MD5") or contains("md5"))] | length')

    if [ "$md5_found" -gt 0 ]; then
        print_result "$test_name" "PASS" ""
        echo "  Found $md5_found MD5 usage(s)"
    else
        print_result "$test_name" "FAIL" "MD5 usage not detected"
    fi
}

# Test 5: Context metadata is present
test_context_metadata() {
    local test_name="Context metadata is present in findings"

    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/violating_project" --json 2>/dev/null || true)

    local has_context
    has_context=$(echo "$output" | jq -r '[.findings[] | select(.context != null)] | length')

    local total_findings
    total_findings=$(echo "$output" | jq -r '.findings | length')

    if [ "$has_context" -eq "$total_findings" ] && [ "$total_findings" -gt 0 ]; then
        print_result "$test_name" "PASS" ""
    else
        print_result "$test_name" "FAIL" "Not all findings have context metadata ($has_context/$total_findings)"
    fi
}

# Test 6: Test code is marked as non-production
test_test_code_detection() {
    local test_name="Test code is marked as non-production"

    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/violating_project" --json 2>/dev/null || true)

    # Check if findings in tests/ directory are marked as non-production
    local test_findings
    test_findings=$(echo "$output" | jq -r '[.findings[] | select(.location.file | contains("tests/"))] | length')

    if [ "$test_findings" -eq 0 ]; then
        print_result "$test_name" "PASS" "No findings in test directory (expected)"
        return
    fi

    local test_findings_marked_non_prod
    test_findings_marked_non_prod=$(echo "$output" | jq -r '[.findings[] | select(.location.file | contains("tests/")) | select(.context.is_test_file == true)] | length')

    if [ "$test_findings_marked_non_prod" -eq "$test_findings" ]; then
        print_result "$test_name" "PASS" ""
    else
        print_result "$test_name" "FAIL" "Test code not properly marked as non-production ($test_findings_marked_non_prod/$test_findings)"
    fi
}

# Test 7: usedforsecurity=False is detected as false positive
test_false_positive_detection() {
    local test_name="usedforsecurity=False detected as lower severity"

    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/violating_project" --json 2>/dev/null || true)

    # Check for findings with usedforsecurity=False mitigation
    local false_positive_findings
    false_positive_findings=$(echo "$output" | jq -r '[.findings[] | select(.false_positive_check.has_mitigation == true)] | length')

    if [ "$false_positive_findings" -gt 0 ]; then
        print_result "$test_name" "PASS" ""
        echo "  Found $false_positive_findings finding(s) with mitigation"
    else
        print_result "$test_name" "FAIL" "usedforsecurity=False not detected as false positive indicator"
    fi
}

# Test 8: Compliant project scan passes
test_compliant_project() {
    local test_name="Compliant project has minimal/no violations"

    if [ ! -d "$FIXTURES_DIR/compliant_project" ]; then
        print_result "$test_name" "FAIL" "Compliant project fixture not found"
        return
    fi

    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/compliant_project" --json 2>/dev/null || true)

    # Allow for runtime violations (FIPS mode might not be enabled)
    # but source code should be clean
    local source_violations
    source_violations=$(echo "$output" | jq -r '[.findings[] | select(.category == "SOURCE_CODE" or .category == "DEPENDENCY")] | length')

    if [ "$source_violations" -eq 0 ]; then
        print_result "$test_name" "PASS" ""
    else
        print_result "$test_name" "FAIL" "Found $source_violations source/dependency violation(s) in compliant project"
    fi
}

# Test 9: JSON output is valid
test_json_validity() {
    local test_name="Scanner outputs valid JSON"

    local output
    output=$("$SCANNER" --path "$FIXTURES_DIR/violating_project" --json 2>/dev/null || true)

    if echo "$output" | jq empty 2>/dev/null; then
        print_result "$test_name" "PASS" ""
    else
        print_result "$test_name" "FAIL" "Scanner output is not valid JSON"
    fi
}

# Test 10: Exit codes are correct
test_exit_codes() {
    local test_name="Scanner returns correct exit codes"

    # Violating project should have non-zero exit code
    "$SCANNER" --path "$FIXTURES_DIR/violating_project" --json >/dev/null 2>&1 || local violating_exit=$?

    if [ "${violating_exit:-0}" -ne 0 ]; then
        print_result "$test_name" "PASS" ""
        echo "  Violating project exit code: ${violating_exit}"
    else
        print_result "$test_name" "FAIL" "Violating project should have non-zero exit code"
    fi
}

# Main test runner
main() {
    echo "═══════════════════════════════════════════════"
    echo " FIPS Python Scanner Integration Tests"
    echo "═══════════════════════════════════════════════"
    echo ""

    # Run tests
    test_scanner_exists
    test_violating_project
    test_pycryptodome_detection
    test_md5_detection
    test_context_metadata
    test_test_code_detection
    test_false_positive_detection
    test_compliant_project
    test_json_validity
    test_exit_codes

    # Print summary
    echo ""
    echo "═══════════════════════════════════════════════"
    echo " Test Summary"
    echo "═══════════════════════════════════════════════"
    echo "Tests run:    $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"

    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
        echo ""
        exit 1
    else
        echo -e "Tests failed: ${GREEN}0${NC}"
        echo ""
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

main "$@"
