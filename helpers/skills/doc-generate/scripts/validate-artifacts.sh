#!/usr/bin/env bash
# Run Vale, asciidoctor, and lychee on specified AsciiDoc files.
# Collects results into structured JSON.
#
# Usage:
#   bash validate-artifacts.sh <file1.adoc> [file2.adoc ...]
#   bash validate-artifacts.sh workspace/repos/opendatahub-io/opendatahub-documentation/modules/**/*.adoc
#
# Output (JSON to stdout):
# {
#   "vale": { "status": "pass|fail|skipped", "findings": [...] },
#   "asciidoctor": { "status": "pass|fail|skipped", "findings": [...] },
#   "lychee": { "status": "pass|fail|skipped", "findings": [...] },
#   "yaml_syntax": { "status": "pass|fail|skipped", "findings": [...] }
# }

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env if available
source "${SCRIPTS_DIR}/load-env.sh"

FILES=("$@")

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo '{"error": "No files specified"}' >&2
    echo '{"vale": {"status": "skipped"}, "asciidoctor": {"status": "skipped"}, "lychee": {"status": "skipped"}, "yaml_syntax": {"status": "skipped"}}'
    exit 0
fi

RESULTS='{}'

# --- Vale ---
if command -v vale >/dev/null 2>&1; then
    VALE_OUTPUT=$(vale --output=JSON "${FILES[@]}" 2>/dev/null || true)
    if [[ -n "$VALE_OUTPUT" && "$VALE_OUTPUT" != "null" ]]; then
        VALE_FINDINGS=$(echo "$VALE_OUTPUT" | jq '[
            to_entries[] | .key as $file | .value[] | {
                file: $file,
                line: .Line,
                severity: (if .Severity == "error" then "high" elif .Severity == "warning" then "medium" else "low" end),
                rule: .Check,
                message: .Message,
                tool: "vale"
            }
        ]' 2>/dev/null || echo '[]')
        VALE_COUNT=$(echo "$VALE_FINDINGS" | jq 'length')
        VALE_STATUS=$(if [[ "$VALE_COUNT" -gt 0 ]]; then echo "fail"; else echo "pass"; fi)
        RESULTS=$(echo "$RESULTS" | jq --arg status "$VALE_STATUS" --argjson findings "$VALE_FINDINGS" \
            '. + {vale: {status: $status, findings: $findings}}')
    else
        RESULTS=$(echo "$RESULTS" | jq '. + {vale: {status: "pass", findings: []}}')
    fi
else
    echo "Warning: vale not found, skipping style checks" >&2
    RESULTS=$(echo "$RESULTS" | jq '. + {vale: {status: "skipped", findings: []}}')
fi

# --- Asciidoctor ---
if command -v asciidoctor >/dev/null 2>&1; then
    ADOC_FINDINGS='[]'
    ADOC_STATUS="pass"
    for file in "${FILES[@]}"; do
        if [[ "$file" == *.adoc ]]; then
            ADOC_ERRORS=$(asciidoctor -o /dev/null -v "$file" 2>&1 || true)
            if [[ -n "$ADOC_ERRORS" ]]; then
                while IFS= read -r line; do
                    if [[ -n "$line" ]]; then
                        # Parse asciidoctor warning/error lines
                        ADOC_FINDINGS=$(echo "$ADOC_FINDINGS" | jq --arg file "$file" --arg msg "$line" \
                            '. + [{file: $file, message: $msg, severity: "medium", tool: "asciidoctor"}]')
                        ADOC_STATUS="fail"
                    fi
                done <<< "$ADOC_ERRORS"
            fi
        fi
    done
    RESULTS=$(echo "$RESULTS" | jq --arg status "$ADOC_STATUS" --argjson findings "$ADOC_FINDINGS" \
        '. + {asciidoctor: {status: $status, findings: $findings}}')
else
    echo "Warning: asciidoctor not found, skipping compilation checks" >&2
    RESULTS=$(echo "$RESULTS" | jq '. + {asciidoctor: {status: "skipped", findings: []}}')
fi

# --- Lychee (link checking) ---
if command -v lychee >/dev/null 2>&1; then
    LYCHEE_FINDINGS='[]'
    LYCHEE_STATUS="pass"
    for file in "${FILES[@]}"; do
        LYCHEE_OUTPUT=$(lychee --format json "$file" 2>/dev/null || true)
        if [[ -n "$LYCHEE_OUTPUT" ]]; then
            FAILED_LINKS=$(echo "$LYCHEE_OUTPUT" | jq -r '.fail[]? // empty' 2>/dev/null || true)
            if [[ -n "$FAILED_LINKS" ]]; then
                while IFS= read -r link; do
                    LYCHEE_FINDINGS=$(echo "$LYCHEE_FINDINGS" | jq --arg file "$file" --arg link "$link" \
                        '. + [{file: $file, message: ("Broken link: " + $link), severity: "medium", tool: "lychee"}]')
                    LYCHEE_STATUS="fail"
                done <<< "$FAILED_LINKS"
            fi
        fi
    done
    RESULTS=$(echo "$RESULTS" | jq --arg status "$LYCHEE_STATUS" --argjson findings "$LYCHEE_FINDINGS" \
        '. + {lychee: {status: $status, findings: $findings}}')
else
    echo "Warning: lychee not found, skipping link checks" >&2
    RESULTS=$(echo "$RESULTS" | jq '. + {lychee: {status: "skipped", findings: []}}')
fi

# --- YAML Syntax ---
YAML_FINDINGS='[]'
YAML_STATUS="pass"
for file in "${FILES[@]}"; do
    # Extract YAML blocks from AsciiDoc files
    if [[ "$file" == *.adoc ]]; then
        # Look for [source,yaml] blocks
        IN_YAML=false
        YAML_BLOCK=""
        LINE_NUM=0
        BLOCK_START=0
        while IFS= read -r line; do
            LINE_NUM=$((LINE_NUM + 1))
            if [[ "$IN_YAML" == true ]]; then
                if [[ "$line" == "----" ]] || [[ "$line" == "====" ]]; then
                    IN_YAML=false
                    if [[ -n "$YAML_BLOCK" ]]; then
                        # Validate YAML
                        if ! echo "$YAML_BLOCK" | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)" 2>/dev/null; then
                            YAML_FINDINGS=$(echo "$YAML_FINDINGS" | jq --arg file "$file" --argjson line "$BLOCK_START" \
                                '. + [{file: $file, line: $line, message: "Invalid YAML syntax in code block", severity: "high", tool: "yaml_syntax"}]')
                            YAML_STATUS="fail"
                        fi
                    fi
                    YAML_BLOCK=""
                else
                    YAML_BLOCK="${YAML_BLOCK}${line}"$'\n'
                fi
            elif [[ "$line" == *"[source,yaml"* ]] || [[ "$line" == *"[source,YAML"* ]]; then
                # Next line should be ---- to start the block
                :
            elif [[ "$line" == "----" ]] && [[ -n "$(sed -n "$((LINE_NUM-1))p" "$file" 2>/dev/null)" ]]; then
                PREV_LINE=$(sed -n "$((LINE_NUM-1))p" "$file" 2>/dev/null || true)
                if [[ "$PREV_LINE" == *"[source,yaml"* ]] || [[ "$PREV_LINE" == *"[source,YAML"* ]]; then
                    IN_YAML=true
                    BLOCK_START=$LINE_NUM
                fi
            fi
        done < "$file" 2>/dev/null || true
    fi
done
RESULTS=$(echo "$RESULTS" | jq --arg status "$YAML_STATUS" --argjson findings "$YAML_FINDINGS" \
    '. + {yaml_syntax: {status: $status, findings: $findings}}')

echo "$RESULTS" | jq '.'
