# vLLM Slack Summary Skill

Automated slack summaries of vLLM CI SIG Slack activity for the Red Hat AI Inference Server (RHAIIS) team.

## Quick Start

```bash
# Run from the skill directory
./scripts/generate_transcript.py
```

## What This Does

1. Exports last week's messages from vLLM CI Slack channel
2. Converts to markdown transcript with proper formatting
3. Outputs for AI analysis and summarization

## Requirements

- `slackdump` CLI tool (authenticated with vLLM workspace)
- Python 3.12+

## Files

```
vllm-slack-summary/
├── SKILL.md                          # Main skill documentation
├── README.md                         # This file
├── scripts/
    └── generate_transcript.py       # Main script
```

## Usage Examples

```bash
# Default (last 7 days, default channel)
./scripts/generate_transcript.py

# Custom time range
./scripts/generate_transcript.py --days 14

# Specify a different channel ID
./scripts/generate_transcript.py --channel C12345ABCDE

# Different output directory
./scripts/generate_transcript.py --output-dir my_summary
```

## Output

Creates `vllm_slack_summary/` directory with:
- `transcript.md` - Formatted conversation transcript
- `slack_export/` - Raw Slack export data

## Workflow

1. **Generate Transcript**
   ```bash
   ./scripts/generate_transcript.py
   ```

2. **Analyze with Claude**
   - Claude reads the transcript
   - Generates summary
   - Highlights critical issues for RHAIIS team

3. **Take Action**
   - Review action items
   - Create JIRA issues if needed
   - Share summary with team

## Integration

This skill works alongside:
- **slackdump** - CLI tool for exporting Slack data
- **Claude Code** - For AI-powered summarization

## Customization

Edit `scripts/generate_transcript.py` to:
- Change default channel ID
- Modify date range
- Adjust output format
- Add additional processing

## Troubleshooting

### "slackdump not found"

```bash
# Install slackdump
brew install slackdump  # macOS
# or download from https://github.com/rusq/slackdump
```

### "Not authenticated"

```bash
slackdump workspace add
```

### "No users.json"

- slackdump export command generates this automatically
- Check that export completed successfully

## Maintenance

- Weekly runs recommended (Tuesday afternoon before SIG CI meeting)
- Review slackdump updates monthly
- Update summary guidance quarterly based on team needs

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
