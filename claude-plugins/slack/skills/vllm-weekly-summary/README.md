# vLLM Weekly Summary Skill

Automated weekly summaries of vLLM CI SIG Slack activity for the Red Hat AI Inference Server (RHAIIS) team.

## Quick Start

```bash
# Run from project root
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py
```

## What This Does

1. Exports last week's messages from vLLM CI Slack channel
2. Converts to markdown transcript with proper formatting
3. Outputs for AI analysis and summarization

## Requirements

- `slackdump` CLI tool (authenticated with vLLM workspace)
- `slack_to_transcript.py` in project root
- Python 3.12+

## Files

```
vllm-weekly-summary/
├── SKILL.md                          # Main skill documentation
├── README.md                         # This file
├── scripts/
│   └── generate_transcript.py       # Main script
└── templates/
    └── summary_template.md          # Template for AI summaries
```

## Usage Examples

```bash
# Default (last 7 days)
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py

# Custom time range
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py --days 14

# Different output directory
.claude/skills/vllm-weekly-summary/scripts/generate_transcript.py --output-dir my_summary
```

## Output

Creates `vllm_weekly_summary/` directory with:
- `transcript.md` - Formatted conversation transcript
- `slack_export/` - Raw Slack export data

## Workflow

1. **Generate Transcript**
   ```bash
   .claude/skills/vllm-weekly-summary/scripts/generate_transcript.py
   ```

2. **Analyze with Claude**
   - Claude reads the transcript
   - Generates structured summary using template
   - Highlights critical issues for RHAIIS team

3. **Take Action**
   - Review action items
   - Create JIRA issues if needed
   - Share summary with team

## Integration

This skill works alongside:
- **slack_to_transcript.py** - Converts Slack exports to markdown
- **slackdump** - CLI tool for exporting Slack data
- **Claude Code** - For AI-powered summarization

## Customization

Edit `scripts/generate_transcript.py` to:
- Change default channel ID
- Modify date range
- Adjust output format
- Add additional processing

## Troubleshooting

**"slackdump not found"**
```bash
# Install slackdump
brew install slackdump  # macOS
# or download from https://github.com/rusq/slackdump
```

**"Not authenticated"**
```bash
slackdump workspace add
```

**"No users.json"**
- slackdump export command generates this automatically
- Check that export completed successfully

## Maintenance

- Weekly runs recommended (Monday mornings)
- Review slackdump updates monthly
- Update template quarterly based on team needs

## Support

For issues:
1. Check `SKILL.md` for detailed documentation
2. Review error messages from slackdump/script
3. Verify prerequisites are installed
4. Check Slack workspace authentication

## Version History

- **1.0.0** (2025-12-09) - Initial release
  - Slack export integration
  - Markdown transcript generation
  - AI summarization workflow
