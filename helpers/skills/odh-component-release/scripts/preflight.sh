#!/usr/bin/env bash
# Preflight: confirm required CLIs are installed and gh is authenticated.
# Prints a human-readable report and exits non-zero if anything is missing.
#
# Usage: preflight.sh [--help]

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
preflight.sh — verify tooling for odh-component-release.

Checks: gh (and gh auth status), yq, jq, skopeo.
Exits 0 when everything is present, non-zero otherwise.

No arguments. No side effects.
EOF
    exit 0
fi

missing=0

check_cmd() {
    local name="$1"
    local install_hint="$2"
    if command -v "${name}" >/dev/null 2>&1; then
        printf '  %-8s ok\n' "${name}:"
    else
        printf '  %-8s MISSING — %s\n' "${name}:" "${install_hint}"
        missing=$((missing + 1))
    fi
}

echo "Tool availability:"
check_cmd gh     "dnf install gh   or brew install gh,   then: gh auth login"
check_cmd yq     "dnf install yq   or brew install yq"
check_cmd jq     "dnf install jq   or brew install jq"
check_cmd skopeo "dnf install skopeo or brew install skopeo"

echo
echo "GitHub auth:"
if command -v gh >/dev/null 2>&1; then
    if gh auth status >/dev/null 2>&1; then
        gh_user=$(gh api user --jq '.login' 2>/dev/null || echo "?")
        echo "  authenticated as ${gh_user}"
    else
        echo "  NOT authenticated — run: gh auth login"
        missing=$((missing + 1))
    fi
else
    echo "  skipped (gh not installed)"
fi

if [ "${missing}" -gt 0 ]; then
    echo
    echo "Preflight: ${missing} issue(s). Install missing tools, then retry." >&2
    exit 1
fi

echo
echo "Preflight: ok"
