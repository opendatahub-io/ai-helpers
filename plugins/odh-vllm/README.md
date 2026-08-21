# odh-vllm

vLLM backport triage, cherry-pick automation, and requirements comparison

## Install

```text
/plugin marketplace add opendatahub-io/ai-helpers
/plugin install odh-vllm@odh-ai-helpers
```

## Skills

- **vllm-backport-check-backported** — Check which candidate PRs have already been cherry-picked into the downstream branch.
- **vllm-backport-cherry-pick** — Auto cherry-pick backport candidates and create a draft PR on the downstream repo.
- **vllm-backport-classify** — Classify bugfix PRs by type (runtime_bug, platform_specific, unclear, not_bugfix) and filter by file existence at a release tag.
- **vllm-backport-fetch-prs** — Fetch merged bugfix PRs from vllm-project/vllm within a date window.
- **vllm-backport-push-report** — Push a triage report to GitHub under a timestamped directory in reports/.
- **vllm-backport-score-rank** — Score and rank backport candidates using a composite formula based on verdict, severity, scope, risk, and self-containedness.
- **vllm-compare-reqs** — Use this skill to compare vllm requirements files between versions.
- **vllm-slack-summary** — Use this skill to generate slack summaries of vLLM CI SIG Slack channel activity for the RHAIIS midstream release team.
