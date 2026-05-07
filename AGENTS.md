# AI Helpers Marketplace

This repository serves as a collaborative marketplace for AI automation tools, plugins, and assistants designed to enhance productivity across multiple AI platforms. It provides a centralized location for sharing and discovering AI-powered development tools.

## Repository Purpose

The odh-ai-helpers repository hosts collections of four distinct tool types:
- **Skills**: Standardized capabilities using agentskills.io format, compatible with Claude Code and Cursor
- **Commands**: Atomic, executable actions for immediate functionality
- **Agents**: Specialized AI entities for complex, multi-step workflows and analysis
- **Gemini Gems**: Conversational AI assistants optimized for specific domains

This enables teams to automate repetitive tasks, integrate with development tools, and create specialized AI capabilities tailored to specific workflows and needs.

## Tool Types

### Skills
Standardized capabilities that work across multiple AI platforms using the agentskills.io specification. Skills provide reusable functionality with cross-platform compatibility.

**→ Located in [helpers/skills/](helpers/skills/) directory**

### Commands
Atomic, executable actions that provide immediate functionality. Commands are designed for quick, specific tasks and can be invoked directly by AI agents.

**→ Located in [helpers/commands/](helpers/commands/) directory**

### Agents
Specialized AI entities capable of complex reasoning and multi-step workflows. Agents maintain context and can execute sophisticated analysis within their domain of expertise.

**→ Located in [helpers/agents/](helpers/agents/) directory**

### Gemini Gems
Conversational AI assistants created within Google's Gemini platform. Each Gem is tailored with specific instructions and knowledge bases for particular domains or tasks.

**→ For detailed Gemini Gems instructions, see [Gemini Gems README](helpers/gems/README.md)**

## Platform Support

### Claude Code
- **Skills**: Available through marketplace plugin entries
- **Commands**: Available through marketplace plugin entries
- **Agents**: Available as sub-agents through marketplace plugin entries


### OpenCode.ai
- **Skills**: Compatible as OpenCode skills in ~/.config/opencode/skills/
- **Commands**: Compatible as OpenCode commands in ~/.config/opencode/commands/
- **Agents**: Not currently compatible due to format differences

### Cursor AI
- **Skills**: Compatible through agentskills.io format
- **Commands**: Can be adapted for Cursor command structure
- **Agents**: Can be used as specialized workflow guides

## How to Create New Tools

### Development Workflow (All Platforms)

0. **Know Your Audience**
   - This repository is for Red Hat associates using RHEL/Fedora and macOS. When referencing upstream documentation, curate rather than copy — only include steps relevant to this audience (eg. include dnf/brew steps, omit apt/nix/etc.)

1. **Plan Your Tool**
   - Identify the specific task or workflow to automate
   - Choose the appropriate platform based on requirements
   - Review existing tools to avoid duplication

2. **Follow Platform Guidelines**
   - Read the platform-specific README for detailed instructions
   - Study existing examples in the respective directories
   - Follow naming and structure conventions

3. **Validate and Test**
   ```bash
   make lint      # Validate tool structure
   make update    # Update settings and website data
   ```

4. **Submit Contribution**
   - Test your tool thoroughly
   - Update relevant documentation
   - Submit a merge request with your changes

## Tool Registry

The marketplace uses a centralized category registry in `categories.yaml` to organize specialized tools by category. **Tools not listed in any category are automatically placed in the "General" category**, providing a clean organization system that requires no action from contributors for basic tools.

### Category Registry Structure

Specialized tool categories are defined in `categories.yaml` at the repository root:

```yaml
CategoryName:
  - specialized-tool
  - another-tool

AnotherCategory:
  - domain-specific-tool
```

## Ethical Guidelines

This project follows strict ethical guidelines for AI tool development, particularly regarding the use of real people's names and personas.

For detailed ethical guidelines and best practices, see [ETHICS.md](ETHICS.md).

## Contributor Quality Checklist

These rules prevent the most common review findings. Follow them when generating or modifying code in this repository.

### General
- Do not create orphaned test files that will never be executed.
- Do not add unnecessary external dependencies in simple scripts.

### Markdown
- Always specify a language identifier on fenced code blocks (` ```bash `, ` ```json `, ` ```yaml `, ` ```python `, etc.). Never use bare ` ``` ` fences.
- Ensure skill names in SKILL.md match the directory name and any registry entry.
- Ensure script paths referenced in instructions match actual file locations.

### Shell Scripts
- Always use `set -euo pipefail`.
- Must pass `shellcheck` with no warnings.
- Quote all variable expansions — never interpolate unsanitized variables into commands.
- Use `mktemp -d` for temporary directories, never hardcoded `/tmp/` paths.
- Do not suppress errors from `gh`, `curl`, or `git` — propagate failures explicitly.
- Use `grep -E` instead of `grep -P` (PCRE is not available on macOS).
- Do not use `git add -A` in scripts — stage specific files only.

### Python Scripts
- Must pass `ruff check` and `ruff format --check`.
- Add timeouts to all HTTP requests (e.g., `requests.get(url, timeout=30)`).
- Do not use bare `except Exception: pass` — log or re-raise errors.
- Validate inputs (ticket keys, URLs, file paths) before use in shell commands or API calls.
- Specify `encoding="utf-8"` when opening files.

### Containerfiles / CI Workflows
- Pin base images by digest, not mutable tags.
- Verify integrity of downloaded binaries (checksum or GPG signature).
- Set explicit `permissions: read-all` on GitHub Actions workflow jobs.
- Pin GitHub Actions to full 40-character commit SHAs, not version tags.
- Pin inline script dependencies to specific versions.

### Skills and Commands
- Run `make update` after creating or modifying any skill, command, or agent.
- `allowed_tools` in frontmatter must follow least-privilege — only list tools the skill actually uses.
- Never reference real people by name (see ETHICS.md).
- Use team/org identifiers in `metadata.author`, not personal names.
- Prefer native CLI tools (`gh`, `glab`, `acli`) via Bash over MCP equivalents for forge and service operations. These CLIs are already available, add no tool schema overhead to the system prompt, and are cheaper on tokens. Provide explicit CLI commands in skill instructions instead of relying on MCP discovery.

## Getting Started

1. **Explore Existing Tools**: Browse [categories.yaml](categories.yaml) for categorized tools or visit our [website](https://opendatahub-io.github.io/ai-helpers/)
2. **Choose Your Platform**: Review platform-specific READMEs for detailed guidance
3. **Study Examples**: Look at existing implementations for structure and patterns
4. **Start Contributing**: Follow the development workflow for your chosen platform
