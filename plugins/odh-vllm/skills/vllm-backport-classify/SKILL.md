---
name: vllm-backport-classify
description: >
  Classify bugfix PRs by type (runtime_bug, platform_specific, unclear, not_bugfix)
  and filter by file existence at a release tag. Use after fetching raw PRs to
  produce a filtered candidate list. PRs marked "unclear" need agent review.
compatibility: Requires gh CLI (authenticated), git, python3
allowed-tools: Bash Read
metadata:
  author: ZhanqiuHu
  version: "1.0"
  tags: vllm, backport, triage
---

# Classify and Filter

Applies deterministic regex rules to classify PRs, checks which files existed
at the target release tag, detects subsystems, and filters out PRs that only
touch post-release or non-runtime code.

## Usage

```bash
python3 scripts/classify-and-filter.py \
  --input artifacts/backport-triage/raw-prs.json \
  --repo /path/to/vllm \
  --tag v0.13.0 \
  --output artifacts/backport-triage/filtered.json
```

## Input

`raw-prs.json` — output of the `vllm-backport-fetch-prs` skill.

## Output

`filtered.json` — same PR objects enriched with:
- `classification`: `runtime_bug`, `platform_specific`, `unclear`, `not_bugfix`
- `verdict`: `CANDIDATE` or `SKIP`
- `skip_reason`: why skipped (if applicable)
- `files`, `files_in_release`, `files_new`, `files_in_release_count`, `files_total`
- `subsystems`: list of detected vLLM subsystem names

## Agent Follow-up

After running this skill, review PRs with `classification: "unclear"`. Read
each PR's description and decide if it's a real bugfix. Override the
classification in the JSON if needed.

Bugfix PRs in vLLM often have misleading titles — always check the actual diff
and description, not just the title.
