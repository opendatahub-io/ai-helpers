---
name: vllm-backport-push-report
description: >
  Push a triage report to GitHub under a timestamped directory in reports/.
  Use after the agent writes the report markdown and has ranked.json ready.
  Outputs the report URL to stdout.
compatibility: Requires git, bash
allowed-tools: Bash
metadata:
  author: ZhanqiuHu
  version: "1.0"
  tags: vllm, backport, triage
---

# Push Report

Creates a timestamped directory under `reports/<version>/`, copies the report
and candidates JSON, commits, pushes, and prints the GitHub URL.

## Usage

```bash
REPORT_URL=$(bash scripts/push-report.sh \
  --report artifacts/backport-triage/report.md \
  --candidates artifacts/backport-triage/ranked.json \
  --version v0.13.0)
```

- **stdout** — the report URL (capture with `$(...)`)
- **stderr** — progress messages

## Error Handling

If `git push` is rejected, try `git pull --rebase` once before retrying.
