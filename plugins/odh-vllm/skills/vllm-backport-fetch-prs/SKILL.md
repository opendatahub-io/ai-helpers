---
name: vllm-backport-fetch-prs
description: >
  Fetch merged bugfix PRs from vllm-project/vllm within a date window.
  Use when starting a backport triage run to get raw PR data from GitHub.
  Outputs a JSON array of PR objects with labels, authors, and merge commits.
compatibility: Requires gh CLI (authenticated), python3, bash
allowed-tools: Bash Read
metadata:
  author: ZhanqiuHu
  version: "1.0"
  tags: vllm, backport, triage
---

# Fetch Bugfix PRs

Fetches merged bugfix PRs from `vllm-project/vllm` using multiple GitHub
search queries (label:bug, [Bugfix]/[BugFix]/[Bug Fix] in title) and
deduplicates results. Also detects reverted PRs.

## Usage

```bash
bash scripts/fetch-bugfix-prs.sh [DAYS_BACK]
```

- `DAYS_BACK` — number of days to look back (default: 7)
- **stdout** — JSON array of PR objects
- **stderr** — progress messages

## Output Schema

Each PR object contains:
- `number`, `title`, `mergedAt`, `mergeCommit.oid`
- `labels`, `author.login`, `mergedBy.login`
- `label_names` — flattened list of label strings
- `reverted_by` — PR number that reverted this one (or null)

## Example

```bash
mkdir -p artifacts/backport-triage
bash scripts/fetch-bugfix-prs.sh 14 > artifacts/backport-triage/raw-prs.json
```

## Determining DAYS_BACK

Check the latest report directory to auto-detect how far back to look:
```bash
LAST=$(ls -1d reports/<version>/*/ 2>/dev/null | tail -1)
```
If no previous report exists, compute days since the release date.
