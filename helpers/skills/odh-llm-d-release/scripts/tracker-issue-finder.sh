#!/usr/bin/env bash
# Find the ODH release tracker issue by loose substring match.
#
# How it matches (NOT a regex against the example title below):
#   1. gh search issues "<--pattern>" --repo <hardcoded> --state open --limit 30
#      Default --pattern is "Release Tracker" so the server returns issues whose
#      title/body contains both tokens.
#   2. Local filter: keep titles whose lowercased form contains BOTH the
#      numeric token from --version (e.g. "3.5") AND, if present, the suffix
#      token (e.g. "ea2"). Bracketing, dashes, and word order don't matter.
#
# Conventional title form (used by humans, not enforced by the matcher):
#   "[Release Tracker] - ODH X.Y[.Z] EAN"
#
# Returns up to 5 candidates.

set -euo pipefail

REPO="opendatahub-io/opendatahub-community"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<EOF
tracker-issue-finder.sh — locate the release tracker issue by fuzzy title match.

Target: ${REPO} (hardcoded)

Required:
  --version <vX.Y-eaN>     ODH release version (e.g. v3.5-ea2)

Optional:
  --pattern <text>         Required token in title (default: "Release Tracker")
  -h, --help               Show this help

Output (stdout, key=value lines):
  count=<n>
  matches=<json>      (JSON array; each entry has number, title, url)
EOF
    exit 0
fi

VERSION=""
PATTERN="Release Tracker"

while [ $# -gt 0 ]; do
    case "$1" in
        --version)   VERSION="$2";  shift 2 ;;
        --pattern)   PATTERN="$2";  shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [ -z "${VERSION}" ]; then
    echo "missing required arg: VERSION" >&2
    exit 2
fi

# Tokens derived from v3.5-ea2 → "3.5" and "ea2".
ver_no_v="${VERSION#v}"
numeric="${ver_no_v%%-*}"          # e.g. "3.5"
suffix=""
if [[ "${ver_no_v}" == *-* ]]; then
    suffix="${ver_no_v#*-}"        # e.g. "ea2"
fi

# Fetch recent open issues containing the pattern. gh search ranks by best
# match; we further filter locally because the tokens vary in casing.
issues_json=$(gh search issues "${PATTERN}" \
    --repo "${REPO}" \
    --state open \
    --limit 30 \
    --json number,title,url \
    2>/dev/null || echo "[]")

matches=$(printf '%s' "${issues_json}" \
    | jq --arg num "${numeric}" --arg sfx "${suffix}" '
        [.[] | select(
            (.title | ascii_downcase | contains($num | ascii_downcase))
            and (($sfx == "") or (.title | ascii_downcase | contains($sfx | ascii_downcase)))
        )] | .[0:5]
      ')

count=$(printf '%s' "${matches}" | jq 'length')
printf 'count=%s\nmatches=%s\n' "${count}" "${matches}"
