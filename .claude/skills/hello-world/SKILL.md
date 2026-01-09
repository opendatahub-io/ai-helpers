---
name: hello-world
description: A simple demonstration skill that greets users and explains how skills work. Use when testing skills or demonstrating skill capabilities.
allowed-tools: Read, Write
---

# Hello World Skill

## Purpose
Demonstrates basic skill structure and activation.

## Instructions

When this skill activates:

1. Greet the user enthusiastically
2. Explain that you're executing via the hello-world skill
3. Show what skills can do:
   - Load instructions dynamically
   - Access supporting files
   - Execute with tool restrictions
   - Compose with other skills

4. Provide a simple example output

## Example Output

```
Hello! 👋 The hello-world skill is now active.

Skills allow me to:
- Load specialized knowledge on demand
- Execute with specific tool permissions
- Work alongside other skills seamlessly

This skill has access to: Read, Write tools only.
```

## Notes

This is a minimal skill demonstrating:
- YAML frontmatter structure
- Tool restrictions via allowed-tools
- Clear activation criteria in description
- Progressive disclosure pattern