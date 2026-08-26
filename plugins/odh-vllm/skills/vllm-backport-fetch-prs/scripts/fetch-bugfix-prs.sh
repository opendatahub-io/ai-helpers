#!/bin/bash
# Fetch bugfix PRs merged into vLLM main within a date window.
# Uses the same search queries as find_backport_candidates.py.
#
# Usage: bash scripts/fetch-bugfix-prs.sh [DAYS_BACK]
# Output: JSON array of PR objects to stdout, status messages to stderr
#
# Requires: gh CLI (authenticated), python3

set -euo pipefail

DAYS_BACK="${1:-7}"
REPO="vllm-project/vllm"
START_DATE=$(date -d "-${DAYS_BACK} days" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

>&2 echo "Fetching bugfix PRs from ${REPO} merged between ${START_DATE} and ${END_DATE}..."

FIELDS="number,title,mergedAt,mergeCommit,labels,author,mergedBy"
WORK=$(mktemp -d)
trap 'rm -rf -- "$WORK"' EXIT

QUERIES=(
  "merged:${START_DATE}..${END_DATE} label:bug"
  "merged:${START_DATE}..${END_DATE} \"[Bugfix]\" in:title"
  "merged:${START_DATE}..${END_DATE} \"[BugFix]\" in:title"
  "merged:${START_DATE}..${END_DATE} \"[Bug Fix]\" in:title"
)

for i in "${!QUERIES[@]}"; do
  gh pr list --repo "$REPO" --state merged --limit 500 \
    --search "${QUERIES[$i]}" \
    --json "$FIELDS" > "${WORK}/batch_${i}.json" 2>/dev/null \
    || echo "[]" > "${WORK}/batch_${i}.json"
  COUNT=$(python3 -c "import json; print(len(json.load(open('${WORK}/batch_${i}.json'))))")
  >&2 echo "  Query $((i+1))/${#QUERIES[@]}: ${COUNT} PRs"
done

gh pr list --repo "$REPO" --state merged --limit 500 \
  --search "merged:${START_DATE}..${END_DATE} \"Revert\" in:title" \
  --json "number,title" > "${WORK}/reverts.json" 2>/dev/null \
  || echo "[]" > "${WORK}/reverts.json"

python3 - "$WORK" << 'PYEOF'
import json, re, sys, glob, os

work = sys.argv[1]
batch_files = sorted(glob.glob(os.path.join(work, "batch_*.json")))

seen = set()
results = []
for f in batch_files:
    for pr in json.load(open(f)):
        if pr["number"] not in seen:
            seen.add(pr["number"])
            results.append(pr)

revert_map = {}
reverts_file = os.path.join(work, "reverts.json")
if os.path.exists(reverts_file):
    for r in json.load(open(reverts_file)):
        for m in re.finditer(r"#(\d+)", r["title"]):
            revert_map[int(m.group(1))] = r["number"]

for pr in results:
    pr["reverted_by"] = revert_map.get(pr["number"])
    label_names = [l.get("name", "") for l in (pr.get("labels") or [])]
    pr["label_names"] = label_names

results.sort(key=lambda p: p.get("mergedAt", ""))
json.dump(results, sys.stdout, indent=2)
print(f"\nTotal: {len(results)} unique bugfix PRs", file=sys.stderr)
PYEOF
