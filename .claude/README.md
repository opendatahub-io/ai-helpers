# Claude Skills Infrastructure

This directory contains the Claude Code skills infrastructure for auto-activation and intelligent skill suggestions.

## Directory Structure

```
.claude/
├── hooks/               # Hook scripts for auto-activation
│   ├── skill_activation_prompt.py    # Analyzes prompts and suggests skills
├── skills/              # Skill definitions and resources
│   └── skill-rules.json
├── commands/            # Custom slash commands (empty, ready to use)
├── settings.json        # Hook configuration
└── README.md           # This file
```

## Setup Instructions

### 1. Python Hooks - No Dependencies Required

This project uses **Python-based hooks** with no external dependencies beyond Python 3.

**No installation required!** The hooks are ready to use.

Verify hook scripts are executable:

```bash
chmod +x .claude/hooks/*.py
```

### 2. Configuration

The hooks are configured in [settings.json](settings.json):

- **UserPromptSubmit**: Triggers `skill_activation_prompt.py` to analyze user prompts and suggest relevant skills

## How Auto-Activation Works

1. **User enters a prompt** → `UserPromptSubmit` hook fires
2. **Hook analyzes prompt** → Matches against patterns in `skill-rules.json`
3. **Skills suggested** → Claude sees relevant skills for the task
4. **Claude activates skill** → Skill instructions loaded into context

## Adding New Skills

1. Create skill directory in `.claude/skills/<skill-name>/`
2. Add `skill.md` with skill instructions
3. Add entry to `skill-rules.json` with trigger patterns
4. Test activation with relevant prompts

### Example skill-rules.json Entry

```json
{
  "my-skill": {
    "type": "domain",
    "enforcement": "suggest",
    "priority": "high",
    "promptTriggers": {
      "keywords": ["keyword1", "keyword2"],
      "intentPatterns": ["pattern.*regex"]
    },
    "fileTriggers": {
      "paths": ["**/*.py"],
      "contentPatterns": ["import torch"]
    }
  }
}
```

### Skill Priority Levels

- **critical**: Required skills (enforcement: block)
- **high**: Strongly recommended
- **medium**: Suggested
- **low**: Optional

## Troubleshooting

### Hook Not Firing

1. Check [settings.json](settings.json) is properly formatted
2. Verify hook scripts are executable (`chmod +x .claude/hooks/*.py`)
3. Verify `$CLAUDE_PROJECT_DIR` environment variable is set
4. Check Python 3 is available (`python3 --version`)

## Reference

Based on: https://github.com/diet103/claude-code-infrastructure-showcase
