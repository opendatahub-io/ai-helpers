# Plugin Hooks

This directory contains Claude Code hooks for the odh-ai-helpers plugin. These hooks enable automatic skill activation suggestions based on user prompts.

## Directory Structure

```
helpers/hooks/
├── hooks.json                    # Hook configuration for the plugin
├── skill_activation_prompt.py   # Analyzes prompts and suggests skills
├── skill-rules.json              # Trigger patterns for skill activation
└── README.md                     # This file
```

## How It Works

When the odh-ai-helpers plugin is installed:

1. **Automatic registration**: The `hooks.json` file registers the `UserPromptSubmit` hook with Claude Code
2. **Prompt analysis**: When users submit prompts, `skill_activation_prompt.py` analyzes them against patterns in `skill-rules.json`
3. **Smart suggestions**: If keywords or patterns match, Claude sees a suggestion to use the relevant skill
4. **Skill activation**: Users can then invoke the suggested skill using the Skill tool

## Files

### hooks.json

Defines the hook configuration for the plugin:

```json
{
  "description": "Automatic skill activation suggestions based on user prompts",
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/skill_activation_prompt.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Key features:**
- Uses `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- Fires on every user prompt submission
- 5-second timeout for fast response

### skill_activation_prompt.py

Python script that:
- Reads user prompt from stdin (JSON format)
- Loads trigger rules from `skill-rules.json`
- Matches keywords and regex patterns
- Outputs suggestions in `additionalContext` format

**No dependencies required** - uses only Python 3 standard library.

### skill-rules.json

Defines trigger patterns for each skill:

```json
{
  "version": "1.0.0",
  "skills": {
    "skill-name": {
      "type": "domain",
      "enforcement": "suggest",
      "priority": "high",
      "promptTriggers": {
        "keywords": ["keyword1", "keyword2"],
        "intentPatterns": ["regex.*pattern"]
      }
    }
  }
}
```

**Priority levels:**
- **critical**: Required skills (shown with ⚠️)
- **high**: Strongly recommended (shown with 📚)
- **medium**: Suggested (shown with 💡)
- **low**: Optional (shown with 📌)

## Adding New Skill Triggers

To add activation triggers for a new skill:

1. **Add entry to skill-rules.json**:
   ```json
   {
     "skills": {
       "your-skill-name": {
         "type": "domain",
         "enforcement": "suggest",
         "priority": "high",
         "promptTriggers": {
           "keywords": ["keyword1", "keyword2"],
           "intentPatterns": ["pattern.*match"]
         }
       }
     }
   }
   ```


## Environment Variables

- `CLAUDE_PLUGIN_ROOT`: Set by Claude Code when running as plugin hook (points to plugin directory)
- `CLAUDE_PROJECT_DIR`: Fallback for local development (points to project directory)

## References

- [Claude Code Hooks Documentation](http://code.claude.com/docs/en/hooks)
