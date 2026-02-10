# Claude Code Plugins

This directory contains standalone Claude Code plugins that don't fit into the skills/commands/agents/gems structure. These are full-featured plugins with hooks, commands, agents, or other specialized functionality.

## Available Plugins

### question-optimizer

Performance optimization plugin that reduces AI thinking time by detecting simple questions and follow-up queries.

**Features:**
- 4-condition question detection algorithm
- Conversation history tracking (last 5 messages)
- Follow-up detection with word matching
- Suggests Haiku model for follow-up questions
- Debug logging for algorithm tuning

**Hook Type:** `userPromptSubmit`

See [question-optimizer/README.md](question-optimizer/README.md) for detailed documentation.

## Contributing

To add a new plugin to this directory:

1. Create a new directory with your plugin name
2. Follow the standard Claude Code plugin structure:
   ```
   your-plugin/
   ├── .claude-plugin/
   │   └── plugin.json
   ├── hooks/           # Optional
   ├── commands/        # Optional
   ├── agents/          # Optional
   ├── skills/          # Optional
   └── README.md
   ```
3. Add your plugin to `.claude-plugin/marketplace.json` in the root
4. Document your plugin thoroughly in its README.md

## Plugin Structure

All plugins in this directory should include:
- `.claude-plugin/plugin.json` - Plugin metadata
- `README.md` - Comprehensive documentation
- At least one of: hooks, commands, agents, or skills

For more information, see the [Claude Code plugins documentation](https://docs.claude.com/en/docs/claude-code/plugins).
