#!/usr/bin/env bash
# Load .env file if present. Source this at the top of any script that
# needs environment variables.
#
# Locates .env via the git repository root (falling back to cwd).
# Only sets variables that are not already defined in the environment,
# so explicit exports always take precedence.
# Keys are validated against a strict pattern to prevent injection.
#
# Usage:
#   source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"

set -euo pipefail

_LOAD_ENV_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_LOAD_ENV_REPO_ROOT="$(git -C "$_LOAD_ENV_SCRIPTS_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)"
_LOAD_ENV_FILE="${ENV_FILE:-${_LOAD_ENV_REPO_ROOT}/.env}"

if [[ -f "$_LOAD_ENV_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and blank lines
        [[ -z "$line" || "$line" == \#* ]] && continue
        # Extract key=value
        if [[ "$line" == *=* ]]; then
            key="${line%%=*}"
            value="${line#*=}"
            # Validate key: must be a valid shell variable name
            if ! [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then
                continue
            fi
            # Remove surrounding quotes from value; quoted values
            # preserve # characters. Only strip inline comments
            # from unquoted values.
            if [[ "$value" == \"*\" ]]; then
                value="${value#\"}" ; value="${value%\"}"
            elif [[ "$value" == \'*\' ]]; then
                value="${value#\'}" ; value="${value%\'}"
            else
                # Strip inline comments (only if preceded by whitespace)
                value="${value%%[[:space:]]#*}"
            fi
            # Only set if not already defined
            if [[ -z "${!key+x}" ]]; then
                export "$key=$value"
            fi
        fi
    done < "$_LOAD_ENV_FILE"
fi

unset _LOAD_ENV_FILE _LOAD_ENV_SCRIPTS_DIR _LOAD_ENV_REPO_ROOT
