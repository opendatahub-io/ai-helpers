---
name: vllm-backport-cherry-pick
description: >
  Auto cherry-pick backport candidates and create a draft PR on the downstream
  repo. Use after scoring to attempt clean cherry-picks for ai-fixable candidates.
  The agent must still do semantic validation on the result.
compatibility: Requires git, gh CLI (authenticated), python3, bash
allowed-tools: Bash Read
metadata:
  author: ZhanqiuHu
  version: "1.0"
  tags: vllm, backport, triage
---

# Cherry Pick

Selects eligible candidates from ranked.json, attempts cherry-pick on each,
and creates a draft PR if any succeed.

## Candidate Selection

A PR is eligible if ALL of:
- `backport_ease == "ai-fixable"`
- `score >= 50`
- `already_backported == false`
- `verdict` is `must_backport` or `likely_relevant`

## Usage

```bash
bash scripts/cherry-pick.sh \
  --input artifacts/backport-triage/ranked.json \
  --downstream /path/to/downstream-repo \
  --branch rhai/0.13.0 \
  --jira-url "https://redhat.atlassian.net/browse/..." \
  --report-url "https://github.com/..." \
  --output artifacts/backport-triage/cherry-pick-result.json
```

## Output

`cherry-pick-result.json`:
```json
{
  "status": "created|skipped",
  "pr_url": "https://...",
  "succeeded": 3,
  "conflicts": 1,
  "results": [{"number": 12345, "title": "...", "score": 85, "status": "success|conflict"}]
}
```

## Agent Follow-up (Required)

After this skill runs, the agent MUST:
1. **Semantic validation** — review the cherry-picked diff, check imports reference
   modules that exist at the target tag, check for calls to post-release functions
2. If issues found, add a comment on the draft PR
3. Update the Jira ticket with the PR link
4. For conflict candidates with score >= 70, add label `ai-autofix-candidate`
