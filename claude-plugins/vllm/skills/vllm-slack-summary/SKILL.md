---
name: vLLM Slack Summary
description: Generate slack summaries of vLLM CI SIG Slack channel activity for the RHAIIS midstream release team
---

# vLLM slack Summary Skill

Automates generating slack summaries of the vLLM CI SIG Slack channel for the Red Hat AI Inference Server (RHAIIS) team.

## Prerequisites

- **slackdump** installed and authenticated with vLLM workspace
  - Install: <https://github.com/rusq/slackdump>
  - Auth: Run `slackdump workspace add`

## Usage

```bash
./scripts/generate_transcript.py                    # Last 7 days (default)
./scripts/generate_transcript.py --days 14          # Custom date range
./scripts/generate_transcript.py --output-dir out   # Custom output directory
```

## Context

When summarizing the transcript, focus on:

- **Breaking changes** affecting the RHAIIS midstream build
- **Hardware issues** with H100, A100, MI300, or B200 GPUs
- **CI/CD infrastructure** changes impacting test reliability
- **Dependencies** changes in build requirements or Python packages
- **Performance regressions** that could affect RHAIIS
- **Upstream releases** and their stability status

## Output

The skill creates `vllm_slack_summary/` containing:

```text
vllm_slack_summary/
├── slack_export/                               # Raw Slack export
├── transcript.md                               # Markdown transcript
└── slack_summary_YYYY-MM-DD_to_YYYY-MM-DD.md  # Summary report
```

After generating the transcript, analyze it and create a summary with:

- Executive Summary (2-3 sentences)
- Key Issues & Resolutions
- CI/CD Infrastructure Changes
- Action Items for Red Hat Team

## Troubleshooting

| Issue | Solution |
|-------|----------|
| slackdump not found | Ensure slackdump is in PATH: `which slackdump` |
| Authentication failed | Run `slackdump workspace add` |
| No messages found | Check date range; channel may have no messages in that period |

## Quick Reference

- **Channel ID**: C07R5PAL2L9 (vLLM CI SIG)
- **Transcript**: `vllm_slack_summary/transcript.md`
- **Summary**: `vllm_slack_summary/slack_summary_YYYY-MM-DD_to_YYYY-MM-DD.md`
