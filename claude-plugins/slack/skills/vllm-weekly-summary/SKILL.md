---
name: vLLM Weekly Summary
description: Generate comprehensive weekly summaries of vLLM CI SIG Slack channel activity for the Red Hat AI Inference Server (RHAIIS) midstream release team
version: 1.0.0
tags:
  - vllm
  - slack
  - ci
  - summary
  - rhaiis
  - midstream
  - weekly-report
when_to_use: |
  Use this skill when:
  - The user asks for a weekly summary of vLLM CI channel
  - The user wants to know what happened in the vLLM community this week
  - The user needs to prepare a status report for the RHAIIS team
  - The user wants to track upstream vLLM CI/CD changes
  - It's time for weekly team sync and you need upstream updates
---

# vLLM Weekly Summary Skill

This skill automates the process of generating comprehensive weekly summaries of the vLLM CI SIG (Special Interest Group - Continuous Integration) Slack channel for the Red Hat AI Inference Server (RHAIIS) midstream release team.

## Overview

The skill performs three main steps:
1. **Export**: Uses `slackdump` CLI to export the last week's messages from the vLLM CI Slack channel
2. **Convert**: Transforms the Slack export into a clean markdown transcript using `slack_to_transcript.py`
3. **Present**: Outputs the transcript for analysis and summarization

## What It Does

- Exports Slack messages from the vLLM CI SIG channel (C07R5PAL2L9)
- Converts messages to markdown format with proper user attribution
- Preserves thread structure for context
- Includes reactions and attachments metadata
- Outputs a transcript ready for AI summarization

## Prerequisites

### Required Tools
- **slackdump** - Must be installed and authenticated with vLLM workspace
  - Installation: See https://github.com/rusq/slackdump
  - Authentication: Run `slackdump workspace add` first
- **slack_to_transcript.py** - Must exist in project root
  - Location: `/Users/whardy/Developer/jira-agent/slack_to_transcript.py`

### Environment Setup
The slackdump tool must be configured with access to the vLLM Slack workspace before using this skill.

## Usage

### Basic Usage
```bash
# Generate summary for the last 7 days
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py
```

### Custom Date Range
```bash
# Generate summary for the last 14 days
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py --days 14
```

### Different Channel
```bash
# Generate summary for a different channel
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py --channel C07R5PAL2L9
```

### Custom Output Directory
```bash
# Specify output directory
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py --output-dir my_summary
```

## Output Structure

The skill creates a directory (default: `vllm_weekly_summary/`) with:

```
vllm_weekly_summary/
├── slack_export/                                    # Raw Slack export data
│   ├── sig-ci/                                     # Channel messages by date
│   │   ├── 2025-12-01.json
│   │   ├── 2025-12-02.json
│   │   └── ...
│   └── users.json                                  # User profile data
├── transcript.md                                   # Formatted markdown transcript
└── weekly_summary_YYYY-MM-DD_to_YYYY-MM-DD.md     # AI-generated summary report
```

## What to Do After Running

After the skill generates the transcript, it will:

1. **Generate the transcript** at `vllm_weekly_summary/transcript.md`
2. **Analyze and create a comprehensive summary** with these focus areas:
   - Executive Summary (2-3 sentences)
   - Key Issues & Resolutions
   - CI/CD Infrastructure Changes
   - Test Failures & Flakes
   - Upstream Dependencies & Breaking Changes
   - Action Items for Red Hat Team
   - Notable Contributors & Discussions
3. **Save the summary to file** at `vllm_weekly_summary/weekly_summary_YYYY-MM-DD_to_YYYY-MM-DD.md`

The summary file is automatically created and ready for distribution to the RHAIIS team.

## Context for Summarization

When summarizing the transcript, consider:

### Project Context
- **vLLM**: Open-source project for efficient LLM serving
- **RHAIIS**: Red Hat AI Inference Server (Red Hat's midstream release of vLLM)
- **CI SIG**: Special Interest Group focused on Continuous Integration infrastructure

### What the RHAIIS Team Cares About
1. **Breaking Changes**: Anything that could affect the midstream build
2. **Hardware Compatibility**: Issues with H100, A100, MI300, B200 GPUs
3. **Test Infrastructure**: CI/CD changes that impact reliability
4. **Release Timing**: Upstream releases and their stability
5. **Dependencies**: Changes in build dependencies or Python packages
6. **Performance Regressions**: Issues that could affect RHAIIS performance

### Red Hat Specific Concerns
- **Hopper (H100) Support**: Critical for Red Hat customers
- **AMD MI300 Support**: Important for AMD partnerships
- **Quantization**: FP8, INT8 support for efficient inference
- **Build System**: Docker, wheel building, packaging issues
- **Regression Detection**: Upstream changes that break functionality

## Example Workflow

```bash
# 1. Run the skill to generate transcript
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py --days 7

# 2. The skill outputs the transcript and context
# 3. Claude analyzes the transcript and provides structured summary
# 4. Summary is automatically saved to weekly_summary_YYYY-MM-DD_to_YYYY-MM-DD.md
# 5. Review and distribute the summary file to the RHAIIS team
```

## Customization Options

### Adjust Time Window
The `--days` parameter controls how far back to look (default: 7 days)

### Change Channel
The `--channel` parameter allows monitoring different Slack channels (default: vLLM CI SIG)

### Output Location
The `--output-dir` parameter specifies where to save the export and transcript

## Troubleshooting

### "slackdump not found"
Ensure slackdump is installed and in your PATH:
```bash
which slackdump
```

### "slack_to_transcript.py not found"
Verify the script exists at the project root:
```bash
ls -la /Users/whardy/Developer/jira-agent/slack_to_transcript.py
```

### "Authentication failed"
Run `slackdump workspace add` to authenticate with the vLLM workspace

### "No messages found"
Check the date range and channel ID. The channel may not have messages in that time period.

## Maintenance

---

## Quick Reference

**Default Command:**
```bash
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py
```

**Output:**
- Transcript: `vllm_weekly_summary/transcript.md`
- Summary Report: `vllm_weekly_summary/weekly_summary_YYYY-MM-DD_to_YYYY-MM-DD.md`
- Export Data: `vllm_weekly_summary/slack_export/`

**Channel ID:** C07R5PAL2L9 (vLLM CI SIG)
