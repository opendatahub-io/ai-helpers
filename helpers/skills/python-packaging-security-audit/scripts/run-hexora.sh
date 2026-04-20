#!/bin/bash
# Run hexora with the tuned rule set for package onboarding security audits.
# Usage: ./run-hexora.sh <repo-path>
# Output: JSON findings on stdout, diagnostics on stderr.
# Exit codes: 0 = ran successfully (may have findings), 1 = hexora unavailable.

set -euo pipefail

repo_path="${1:?Usage: $0 <repo-path>}"
script_dir="$(cd "$(dirname "$0")" && pwd)"

# Default hexora config is based on data analysis done in AIPCC-13294. Modify as needed.
HEXORA_ARGS=(
  audit "$repo_path"
  --output-format json
  --min-confidence medium
  --exclude HX1000  # AppEnumeration          — app discovery common in dev tools
  --exclude HX1020  # PathEnumeration         — path inspection used in build scripts
  --exclude HX1030  # OSFingerprint           — platform detection used in cross-platform packages
  --exclude HX3010  # ShellExec               — subprocess calls ubiquitous in build tooling
  --exclude HX3040  # DLLInjection            — ctypes.LoadLibrary common in native extensions
  --exclude HX5000  # DunderImport            — __import__ used in plugin/compatibility code
  --exclude HX5010  # SuspiciousImport        — standard library imports (os, sys, shutil, etc.)
  --exclude HX5020  # CtypesImport            — ctypes import common in native extension wrappers
  --exclude HX5030  # PickleImport            — pickle import common in ML/data packages
  --exclude HX5040  # StructImport            — struct import common in binary protocol packages
  --exclude HX5050  # SocketImport            — socket import common in networking packages
  --exclude HX6020  # HexedString             — hex strings common in crypto/hash libraries
  --exclude HX6030  # IntLiterals             — integer arrays common in lookup tables and codecs
  --exclude HX6040  # CVEInLiteral            — CVE references in test fixtures and changelogs
  --exclude HX6060  # PathTraversal           — "../" in path handling code
  --exclude HX7000  # SuspiciousFunctionName  — naming heuristics with high false-positive rate
  --exclude HX7010  # SuspiciousParameterName — naming heuristics with high false-positive rate
  --exclude HX7020  # SuspiciousVariable      — naming heuristics with high false-positive rate
)

if command -v hexora >/dev/null 2>&1; then
  hexora "${HEXORA_ARGS[@]}"
elif command -v uvx >/dev/null 2>&1; then
  uvx --with-requirements "$script_dir/requirements.txt" hexora "${HEXORA_ARGS[@]}"
else
  echo "ERROR: neither hexora nor uvx found" >&2
  exit 1
fi
