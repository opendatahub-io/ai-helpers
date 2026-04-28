# Contributing to AI Helpers

Thank you for your interest in contributing to the AI Helpers marketplace! This repository thrives on community contributions, whether you're adding a new skill, fixing a bug, improving documentation, or sharing an idea.

## Table of Contents

- [Getting Started](#getting-started)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Creating a New Tool](#creating-a-new-tool)
- [Submitting Your Contribution](#submitting-your-contribution)
- [Pull Request Process](#pull-request-process)
- [Style and Conventions](#style-and-conventions)
- [Code of Conduct](#code-of-conduct)
- [Getting Help](#getting-help)

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/<your-username>/ai-helpers.git
   cd ai-helpers
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b my-new-tool
   ```

If you're new to the project, start by browsing the [marketplace website](https://opendatahub-io.github.io/ai-helpers/) and the existing tools in the `helpers/` directory to see how things are structured.

## Ways to Contribute

### Share an Idea

Have an idea but not sure how to implement it? [Open an Idea issue](https://github.com/opendatahub-io/ai-helpers/issues/new?assignees=&labels=enhancement%2Chelp+wanted%2Cidea&template=07_idea_request.md&title=%5BIdea%5D+). No implementation details needed -- just describe what you'd like to automate or improve, and the community will help figure out the best approach.

### Add a New Tool

This is the most common type of contribution. The repository hosts four tool types:

| Type | Location | Format |
|------|----------|--------|
| **Skills** | `helpers/skills/<name>/` | Directory with `SKILL.md` and optional `scripts/` |
| **Commands** | `helpers/commands/` | Single Markdown file |
| **Agents** | `helpers/agents/` | Single Markdown file |
| **Gemini Gems** | `helpers/gems/` | Entry in `gems.yaml` |

### Fix a Bug or Improve Existing Tools

Browse [open issues](https://github.com/opendatahub-io/ai-helpers/issues) for things to work on. Comment `/assign` on an issue to claim it.

### Improve Documentation

Documentation improvements are always welcome, from fixing typos to adding usage examples.

## Development Setup

### Prerequisites

- **Python 3** with [ruff](https://docs.astral.sh/ruff/) (`pip install ruff`)
- **Container runtime**: [Podman](https://podman.io/) or Docker (for running the linter)
- **shellcheck** (`dnf install ShellCheck` on Fedora)
- **Git**

### Validate Your Changes

Before submitting, always run:

```bash
make update    # Regenerate settings and website data -- commit any changes it produces
make lint      # Run all linters and validation checks
```

Run `make update` first and **commit any generated changes** before running `make lint`. The `lint` target re-runs `make update` internally and will fail if there are uncommitted diffs.

The `lint` target runs:
- **claudelint** -- validates plugin structure
- **ruff** -- checks and formats Python code
- **shellcheck** -- lints shell scripts
- Verifies that `make update` produces no uncommitted changes

### Test Locally (Claude Code)

To test a skill or command with Claude Code before submitting:

1. Open `claude`
2. Run `/plugin marketplace add ./`
3. Run `/plugin` then install the local plugin
4. Test your tool
5. Remove the local marketplace when done testing

## Creating a New Tool

### Skills

Skills are the most full-featured tool type. Create a new directory under `helpers/skills/`:

```text
helpers/skills/my-skill/
├── SKILL.md          # Required: skill definition with frontmatter
└── scripts/          # Optional: supporting scripts
    └── run.py
```

The `SKILL.md` file must include YAML frontmatter. Required fields are `name` and `description`; all others are optional:

```yaml
---
name: my-skill                    # Required
description: >                    # Required
  A clear description of what the skill does and when to use it.
allowed-tools: Bash Read Grep Glob
---
```

Common optional fields:

| Field | Purpose |
|-------|---------|
| `allowed-tools` | Tools the skill can use (e.g., `Bash Read Grep Glob`) |
| `user-invocable` | Set to `true` if users can invoke directly via `/skill-name` |
| `argument-hint` | Describes arguments the skill accepts |
| `model` | Specify a model preference (e.g., `sonnet`) |
| `effort` | Set reasoning effort level |
| `compatibility` | List runtime requirements (e.g., `python3, git`) |
| `metadata` | Block for `author`, `version`, and `tags` |

Study existing skills in `helpers/skills/` for examples of structure and patterns.

### Commands

Commands are single Markdown files in `helpers/commands/`:

```text
helpers/commands/my-command.md
```

See `helpers/commands/hello-world-echo.md` for an example.

### Agents

Agents are Markdown files in `helpers/agents/`:

```text
helpers/agents/my-agent.md
```

### Gemini Gems

Add your Gem to `helpers/gems/gems.yaml`. See the [Gemini Gems README](helpers/gems/README.md) for details.

### Categorization

Tools are automatically placed in the "General" category. If your tool belongs to a specialized category, add it to `categories.yaml`:

```yaml
YourCategory:
  - my-tool-name
```

## Submitting Your Contribution

1. **Run validation** before committing:
   ```bash
   make update
   make lint
   ```
2. **Commit your changes** with a clear, descriptive commit message.
3. **Push to your fork** and open a Pull Request against `main`.
4. **Fill out the PR template** -- it will guide you through the required information.

### Commit Messages

Write concise commit messages that explain *why* the change was made. Use a prefix that reflects the type of change:

- `feat:` for new tools or features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `chore:` for maintenance tasks

Example: `feat: add Python dependency resolver skill`

## Pull Request Process

1. **All PRs must pass CI checks**, including `make lint`.
2. **Fill out the PR template completely**, including:
   - Summary of changes
   - Type of contribution
   - Testing and validation checklist
   - Ethical guidelines compliance
3. **At least one maintainer review** is required before merging. [Mergify](https://mergify.com) automatically adds PRs to the merge queue when CI passes and: maintainer-authored PRs have one approval, or other PRs have two approvals.
4. **Respond to review feedback** promptly. Reviewers may ask for changes or have questions.
5. **Keep PRs focused** -- one tool or logical change per PR makes review easier.

### What Reviewers Look For

- Tool works as described and has been tested
- `make lint` passes cleanly
- `make update` was run and any generated changes are committed
- Follows naming conventions and directory structure
- No hardcoded secrets, tokens, or credentials
- Python scripts have proper shebang lines and are executable
- Complies with [ethical guidelines](ETHICS.md)

## Style and Conventions

### Naming

- Use lowercase kebab-case for tool names: `my-tool-name`
- Be descriptive but concise: `python-packaging-license-checker` over `checker`

### Python

- Format with `ruff format`
- Pass `ruff check` with no errors
- Use PEP 723 inline metadata for script dependencies when applicable
- Include proper shebang lines (e.g., `#!/usr/bin/env python3`)

### Shell Scripts

- Pass `shellcheck` with no errors
- Make scripts executable (`chmod +x`)

### Ethical Guidelines

All contributions must comply with our [ethical guidelines](ETHICS.md). In particular:
- **Do not** use real people's names to instruct AI to replicate their style, voice, or persona
- **Do** describe desired qualities explicitly instead of referencing individuals as a proxy

## Code of Conduct

We are committed to providing a welcoming and respectful environment for everyone. Be kind, constructive, and professional in all interactions -- issues, pull requests, and code reviews alike.

## Getting Help

- **Questions about contributing?** Open a [blank issue](https://github.com/opendatahub-io/ai-helpers/issues/new) or reach out to the maintainers.
- **Not sure which tool type to use?** Review the [README](README.md) for descriptions of each type, or open an [Idea issue](https://github.com/opendatahub-io/ai-helpers/issues/new?assignees=&labels=enhancement%2Chelp+wanted%2Cidea&template=07_idea_request.md&title=%5BIdea%5D+) and we'll help.
- **Using AI to develop tools is encouraged!** This is an AI tools repository -- using Claude Code, Cursor, or other AI assistants to help build your contribution is perfectly fine.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
