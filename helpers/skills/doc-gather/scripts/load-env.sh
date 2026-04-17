#!/usr/bin/env bash
# Load .env file if present. Source this at the top of any script that
# needs environment variables.
#
# Searches for .env in the current working directory (project root).
# Only sets variables that are not already defined in the environment,
# so explicit exports always take precedence.
#
# Usage:
#   source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"

_LOAD_ENV_FILE="$(pwd)/.env"

if [[ -f "$_LOAD_ENV_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and blank lines
        [[ -z "$line" || "$line" == \#* ]] && continue
        # Strip inline comments (only if preceded by whitespace)
        line="${line%%[[:space:]]#*}"
        # Extract key=value
        if [[ "$line" == *=* ]]; then
            key="${line%%=*}"
            value="${line#*=}"
            # Remove surrounding quotes from value
            value="${value#\"}" ; value="${value%\"}"
            value="${value#\'}" ; value="${value%\'}"
            # Only set if not already defined
            if [[ -z "${!key+x}" ]]; then
                export "$key=$value"
            fi
        fi
    done < "$_LOAD_ENV_FILE"
fi

unset _LOAD_ENV_FILE
