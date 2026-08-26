---
name: vllm-backport-check-backported
description: >
  Check which candidate PRs have already been cherry-picked into the downstream
  branch. Use after classify-and-filter to mark already_backported on each PR.
  Fully deterministic — compares merge SHAs and PR titles.
compatibility: Requires git, gh CLI (authenticated), python3, bash
allowed-tools: Bash Read
metadata:
  author: ZhanqiuHu
  version: "1.0"
  tags: vllm, backport, triage
---

# Check Backported

Scans the downstream repo's git history and merged PRs to detect which
upstream bugfixes have already been backported.

## Detection Methods

1. **SHA match** — `git log --grep="cherry picked from commit"` on the downstream branch
2. **Title match** — `gh pr list --state merged --base <branch>` title contains `#<number>`

## Usage

```bash
bash scripts/check-backported.sh \
  --input artifacts/backport-triage/filtered.json \
  --downstream /path/to/downstream-repo \
  --branch rhai/0.13.0 \
  --output artifacts/backport-triage/candidates.json
```

## Output

`candidates.json` — same as input with `already_backported: true/false` added
to each PR object. Prints match counts to stderr.
