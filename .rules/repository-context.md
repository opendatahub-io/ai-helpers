# Repository Context

This is the **AI Helpers Marketplace** — a collaborative repository for AI automation tools used by Red Hat associates on RHEL/Fedora and macOS.

## Tool Types

- **Skills** (`helpers/skills/`): Cross-platform capabilities using agentskills.io format
- **Commands** (`helpers/commands/`): Atomic executable actions  
- **Agents** (`helpers/agents/`): Complex multi-step workflow specialists
- **Gemini Gems** (`helpers/gems/`): Google Gemini conversational assistants

## Target Audience

Red Hat associates using RHEL/Fedora and macOS. When reviewing documentation:
- Include `dnf`/`brew` installation steps
- Omit `apt`/`nix`/other package managers
- Focus on enterprise Linux and macOS compatibility

## Key Files

- `categories.yaml`: Tool categorization registry
- `docs/data.json`: Generated plugin metadata (updated via `make update`)
- `ETHICS.md`: Ethical guidelines for AI tool development
- `AGENTS.md`: Full contributor documentation