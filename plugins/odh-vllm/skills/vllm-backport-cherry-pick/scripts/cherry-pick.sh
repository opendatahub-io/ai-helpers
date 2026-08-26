#!/bin/bash
# Auto cherry-pick backport candidates and create a draft PR.
#
# Reads ranked.json, selects ai-fixable candidates, attempts cherry-pick on
# each, creates a draft PR with results.
#
# Usage:
#   bash scripts/cherry-pick.sh \
#     --input artifacts/backport-triage/ranked.json \
#     --downstream /path/to/nm-vllm-ent \
#     --branch rhai/0.13.0 \
#     --jira-url "https://redhat.atlassian.net/browse/..." \
#     --report-url "https://github.com/..." \
#     --output artifacts/backport-triage/cherry-pick-result.json
#
# Output: cherry-pick-result.json with per-PR status and PR URL.

set -euo pipefail

INPUT=""
DOWNSTREAM=""
BRANCH=""
JIRA_URL=""
REPORT_URL=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)      INPUT="$2"; shift 2;;
    --downstream) DOWNSTREAM="$2"; shift 2;;
    --branch)     BRANCH="$2"; shift 2;;
    --jira-url)   JIRA_URL="$2"; shift 2;;
    --report-url) REPORT_URL="$2"; shift 2;;
    --output)     OUTPUT="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "$INPUT" || -z "$DOWNSTREAM" || -z "$BRANCH" || -z "$OUTPUT" ]]; then
  echo "Usage: cherry-pick.sh --input FILE --downstream PATH --branch BRANCH --output FILE" >&2
  exit 1
fi

BACKPORT_DATE=$(TZ="America/New_York" date +"%Y-%m-%d")
BRANCH_NAME="backport/auto-${BACKPORT_DATE}"
UPSTREAM_REPO="vllm-project/vllm"
DOWNSTREAM_REPO=$(git -C "$DOWNSTREAM" remote get-url origin \
  | sed -E 's|.*github.com[:/](.*)\.git$|\1|; s|.*github.com[:/](.*)$|\1|')

# Select candidates: ai-fixable, score >= 50, not already backported
SELECTED=$(python3 - "$INPUT" << 'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    prs = json.load(f)
candidates = [p for p in prs
    if p.get('backport_ease') == 'ai-fixable'
    and p.get('score', 0) >= 50
    and not p.get('already_backported')
    and p.get('verdict') in ('must_backport', 'likely_relevant')]
json.dump(candidates, sys.stdout)
PYEOF
)

COUNT=$(echo "$SELECTED" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")

if [[ "$COUNT" -eq 0 ]]; then
  >&2 echo "No candidates eligible for cherry-pick."
  echo '{"status": "skipped", "reason": "no eligible candidates", "pr_url": null, "results": []}' > "$OUTPUT"
  exit 0
fi

>&2 echo "Selected $COUNT candidates for cherry-pick"

cd "$DOWNSTREAM"
git fetch origin "$BRANCH"
git checkout -b "$BRANCH_NAME" "origin/$BRANCH"

CHERRY_ERR=$(mktemp)
trap 'rm -f -- "$CHERRY_ERR"' EXIT

RESULTS="[]"
SUCCEEDED=0
FAILED=0

echo "$SELECTED" | python3 -c "
import json, sys
for pr in json.load(sys.stdin):
    print(json.dumps({'number': pr['number'], 'title': pr['title'], 'score': pr.get('score', 0)}))
" | while IFS= read -r ROW; do
  PR_NUM=$(echo "$ROW" | python3 -c "import json,sys; print(json.load(sys.stdin)['number'])")
  PR_TITLE=$(echo "$ROW" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'])")

  >&2 echo "  Cherry-picking #${PR_NUM}: ${PR_TITLE:0:60}..."

  MERGE_SHA=$(gh pr view "$PR_NUM" --repo "$UPSTREAM_REPO" --json mergeCommit --jq '.mergeCommit.oid')
  if [[ -z "$MERGE_SHA" || "$MERGE_SHA" == "null" ]]; then
    >&2 echo "    ⚠️ No merge SHA for #${PR_NUM}, skipping"
    FAILED=$((FAILED + 1))
    echo "$ROW" >> "$CHERRY_ERR.skipped"
    continue
  fi

  if git cherry-pick "$MERGE_SHA" --no-commit 2>"$CHERRY_ERR"; then
    git add -A
    SUCCEEDED=$((SUCCEEDED + 1))
    echo "$ROW" >> "$CHERRY_ERR.success"
    >&2 echo "    ✅ Clean"
  else
    git cherry-pick --abort 2>/dev/null || true
    FAILED=$((FAILED + 1))
    echo "$ROW" >> "$CHERRY_ERR.conflict"
    >&2 echo "    ❌ Conflict"
  fi
done

# Build RESULTS from temp files (while-loop runs in subshell, so vars don't propagate)
RESULTS=$(python3 - "${CHERRY_ERR}.success" "${CHERRY_ERR}.conflict" "${CHERRY_ERR}.skipped" << 'PYEOF'
import json, sys, os
results = []
for path, status in [(sys.argv[1], "success"), (sys.argv[2], "conflict"), (sys.argv[3], "skipped")]:
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                row = json.loads(line.strip())
                row["status"] = status
                results.append(row)
json.dump(results, sys.stdout)
PYEOF
)
SUCCEEDED=$(echo "$RESULTS" | python3 -c "import json,sys; print(sum(1 for r in json.load(sys.stdin) if r['status']=='success'))")
FAILED=$(echo "$RESULTS" | python3 -c "import json,sys; print(sum(1 for r in json.load(sys.stdin) if r['status']!='success'))")

if [[ "$SUCCEEDED" -eq 0 ]]; then
  >&2 echo "All candidates had conflicts. Cleaning up branch."
  git checkout - 2>/dev/null || true
  git branch -D "$BRANCH_NAME" 2>/dev/null || true
  echo "$RESULTS" | python3 -c "
import json, sys
results = json.load(sys.stdin)
json.dump({'status': 'skipped', 'reason': 'all candidates had conflicts', 'pr_url': None, 'results': results}, sys.stdout, indent=2)
" >"$OUTPUT"
  exit 0
fi

git commit -m "[Backport] Auto cherry-pick ${BACKPORT_DATE}

Cherry-picked ${SUCCEEDED} commits from ${UPSTREAM_REPO} main → ${BRANCH}.
Skipped ${FAILED} due to conflicts.

Auto-generated by vLLM Backport Triage Bot (Claude on ACP).
Human review required before merging."

git push origin "$BRANCH_NAME"

# Build PR body — pass all untrusted data via stdin/env to avoid injection
PR_BODY=$(echo "$RESULTS" | \
  UPSTREAM_REPO="$UPSTREAM_REPO" \
  BACKPORT_DATE="$BACKPORT_DATE" \
  BRANCH="$BRANCH" \
  JIRA_URL="$JIRA_URL" \
  REPORT_URL="$REPORT_URL" \
  python3 -c "
import json, sys, os

results = json.load(sys.stdin)
upstream = os.environ['UPSTREAM_REPO']
date = os.environ['BACKPORT_DATE']
branch = os.environ['BRANCH']
jira_url = os.environ.get('JIRA_URL', '')
report_url = os.environ.get('REPORT_URL', '')

succeeded = [r for r in results if r['status'] == 'success']
conflicts = [r for r in results if r['status'] != 'success']

body = f'''> [!NOTE]
> **This PR was auto-generated by the vLLM Backport Triage Bot (Claude on ACP).**
> All cherry-picks applied cleanly but require human review before merging.
> The account used to push this PR belongs to a human developer — the actual
> author is an AI agent running on the Ambient Code Platform.

## Auto Backport — {date}

### ✅ Cherry-picked successfully

| # | PR | Title | Score |
|---|---|---|---|
'''

for i, r in enumerate(succeeded):
    title = r['title'][:60].replace('|', '\\\\|')
    body += f'| {i+1} | [#{r[\"number\"]}](https://github.com/{upstream}/pull/{r[\"number\"]}) | {title} | {r[\"score\"]} |\n'

if conflicts:
    body += '''
### ❌ Skipped (conflicts)

| PR | Title | Score |
|---|---|---|
'''
    for r in conflicts:
        title = r['title'][:60].replace('|', '\\\\|')
        body += f'| [#{r[\"number\"]}](https://github.com/{upstream}/pull/{r[\"number\"]}) | {title} | {r[\"score\"]} |\n'

body += f'''
### Review Checklist

- [ ] CI passes on this branch
- [ ] Each cherry-picked change makes sense in the context of {branch}
- [ ] No references to functions/classes/modules added after the release
- [ ] No missing dependencies on other un-backported PRs
- [ ] Quick smoke test: \`python -c \"import vllm\"\` passes on this branch
'''

if jira_url:
    body += f'\n- **Jira ticket**: {jira_url}\n'
if report_url:
    body += f'- **Full report**: [{report_url}]({report_url})\n'

body += '''
---
*Auto-generated by vLLM Backport Triage Bot (Claude on ACP). Human review required.*
'''

print(body)
")

PR_URL=$(gh pr create --repo "$DOWNSTREAM_REPO" \
  --draft \
  --base "$BRANCH" \
  --head "$BRANCH_NAME" \
  --title "[Backport Auto ${BACKPORT_DATE}] ${SUCCEEDED} cherry-picks for ${BRANCH}" \
  --body "$PR_BODY")

>&2 echo "Created draft PR: $PR_URL"

echo "$RESULTS" | \
  PR_URL="$PR_URL" \
  SUCCEEDED="$SUCCEEDED" \
  FAILED="$FAILED" \
  python3 -c "
import json, sys, os
results = json.load(sys.stdin)
json.dump({
    'status': 'created',
    'pr_url': os.environ['PR_URL'],
    'succeeded': int(os.environ['SUCCEEDED']),
    'conflicts': int(os.environ['FAILED']),
    'results': results
}, sys.stdout, indent=2)
" >"$OUTPUT"

>&2 echo "Output: $OUTPUT"
