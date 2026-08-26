---
name: vllm-backport-score-rank
description: >
  Score and rank backport candidates using a composite formula based on
  verdict, severity, scope, risk, and self-containedness. Use after the agent
  completes semantic analysis to produce a prioritized ranked list.
compatibility: Requires python3
allowed-tools: Bash Read
metadata:
  author: ZhanqiuHu
  version: "1.0"
  tags: vllm, backport, triage
---

# Score and Rank

Applies a deterministic scoring formula to produce reproducible rankings.

## Scoring Formula

| Field | Values and Points |
|---|---|
| verdict | must_backport=30, likely_relevant=20, needs_review=10, likely_skip/skip=0 |
| severity | critical=25, moderate=15, low=5 |
| affected_scope | all_users=20, specific_models=12, specific_feature=8, edge_case=3 |
| backport_risk | safe=15, moderate=8, risky=0 |
| self_contained | true=10, false=0 |

**Max score: 100.** Sorted by score desc, then files_in_release desc, then change_size asc.

Each PR also gets `backport_ease`: `ai-fixable` if self_contained AND risk is safe/moderate.

## Usage

```bash
python3 scripts/score-and-rank.py \
  --input artifacts/backport-triage/analyzed.json \
  --output artifacts/backport-triage/ranked.json
```

## Input

`analyzed.json` — candidates with agent-added fields: `verdict`, `severity`,
`affected_scope`, `backport_risk`, `self_contained`.

## Output

`ranked.json` — filtered (removes SKIP/already_backported), scored, sorted,
with `rank`, `score`, `change_size`, `backport_ease` added.
