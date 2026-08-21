#!/bin/bash
# Check which candidate PRs have already been backported to the downstream branch.
#
# Reads filtered.json, checks downstream repo for cherry-picked commits and
# matching PR titles, marks each PR as already_backported true/false.
#
# Usage:
#   bash scripts/check-backported.sh \
#     --input artifacts/backport-triage/filtered.json \
#     --downstream /path/to/nm-vllm-ent \
#     --branch rhai/0.13.0 \
#     --output artifacts/backport-triage/candidates.json
#
# Output: JSON to --output with already_backported field added.
# Requires: git, gh, python3

set -euo pipefail

INPUT=""
DOWNSTREAM=""
BRANCH=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)      INPUT="$2"; shift 2;;
    --downstream) DOWNSTREAM="$2"; shift 2;;
    --branch)     BRANCH="$2"; shift 2;;
    --output)     OUTPUT="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "$INPUT" || -z "$DOWNSTREAM" || -z "$BRANCH" || -z "$OUTPUT" ]]; then
  echo "Usage: check-backported.sh --input FILE --downstream PATH --branch BRANCH --output FILE" >&2
  exit 1
fi

WORK=$(mktemp -d)
trap 'rm -rf -- "$WORK"' EXIT

git -C "$DOWNSTREAM" rev-parse --verify "$BRANCH" >/dev/null 2>&1 \
  || { echo "Error: branch '$BRANCH' not found in $DOWNSTREAM" >&2; exit 1; }

>&2 echo "Building backported SHA set from ${DOWNSTREAM} branch ${BRANCH}..."

git -C "$DOWNSTREAM" log --oneline "$BRANCH" --grep="cherry picked from commit" \
  | grep -oP '(?<=cherry picked from commit )[a-f0-9]+' > "$WORK/shas.txt" \
  || true

>&2 echo "  Found $(wc -l < "$WORK/shas.txt") cherry-picked SHAs"

>&2 echo "Fetching downstream backport PR titles..."
DOWNSTREAM_REPO=$(git -C "$DOWNSTREAM" remote get-url origin 2>/dev/null \
  | sed -E 's|.*github.com[:/](.*)\.git$|\1|; s|.*github.com[:/](.*)$|\1|')

if ! gh pr list --repo "$DOWNSTREAM_REPO" --state merged --base "$BRANCH" --limit 500 \
  --json number,title --jq '.[].title' > "$WORK/titles.txt" 2>/dev/null; then
  >&2 echo "Warning: gh pr list failed for $DOWNSTREAM_REPO — treating as no downstream PRs"
  : > "$WORK/titles.txt"
fi

>&2 echo "  Found $(wc -l < "$WORK/titles.txt") downstream PRs"

python3 - "$INPUT" "$WORK/shas.txt" "$WORK/titles.txt" "$OUTPUT" << 'PYEOF'
import json, sys

input_path, shas_path, titles_path, output_path = sys.argv[1:5]

with open(input_path) as f:
    prs = json.load(f)

with open(shas_path) as f:
    backported_shas = set(line.strip() for line in f if line.strip())

with open(titles_path) as f:
    backport_titles = f.read()

matched = 0
for pr in prs:
    sha = (pr.get("mergeCommit") or {}).get("oid", "")
    num = pr["number"]
    is_backported = (
        sha in backported_shas
        or any(s.startswith(sha[:12]) for s in backported_shas if sha)
        or f"#{num}" in backport_titles
    )
    pr["already_backported"] = is_backported
    if is_backported:
        matched += 1

print(f"Already backported: {matched}/{len(prs)}", file=sys.stderr)

with open(output_path, "w") as f:
    json.dump(prs, f, indent=2)

print(f"Output: {output_path}", file=sys.stderr)
PYEOF
