#!/bin/bash
# Push triage report to GitHub under a timestamped directory.
#
# Usage:
#   bash scripts/push-report.sh \
#     --report artifacts/backport-triage/report.md \
#     --candidates artifacts/backport-triage/ranked.json \
#     --version v0.13.0
#
# Output: prints the report URL to stdout.

set -euo pipefail

REPORT=""
CANDIDATES=""
VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report)     REPORT="$2"; shift 2;;
    --candidates) CANDIDATES="$2"; shift 2;;
    --version)    VERSION="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "$REPORT" || -z "$CANDIDATES" || -z "$VERSION" ]]; then
  echo "Usage: push-report.sh --report FILE --candidates FILE --version VERSION" >&2
  exit 1
fi

if [[ "$VERSION" =~ \.\. || "$VERSION" =~ ^/ || ! "$VERSION" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "Error: VERSION must be alphanumeric (e.g. v0.13.0), got: $VERSION" >&2
  exit 1
fi

TIMESTAMP=$(TZ="America/New_York" date +"%Y-%m-%d_%H-%M-%S_EDT")
REPORT_DIR="reports/${VERSION}/${TIMESTAMP}"

mkdir -p "${REPORT_DIR}"
cp "$REPORT" "${REPORT_DIR}/report.md"
cp "$CANDIDATES" "${REPORT_DIR}/candidates.json"

git add "${REPORT_DIR}"
git commit -m "Triage report ${TIMESTAMP}"
git push

REMOTE_URL=$(git remote get-url origin | sed -E 's|.*github.com[:/](.*)\.git$|\1|; s|.*github.com[:/](.*)$|\1|')
REPORT_URL="https://github.com/${REMOTE_URL}/blob/main/${REPORT_DIR}/report.md"

>&2 echo "Pushed report to ${REPORT_DIR}/"
echo "$REPORT_URL"
