# AI Helpers Collection

This directory contains the core collection of AI automation tools, plugins, and assistants designed to enhance productivity across multiple AI platforms. The tools are organized into four distinct categories, each serving different purposes and platforms.

## Directory Structure

```text
helpers/
├── agents/     # Specialized AI entities for complex workflows
├── commands/   # Atomic, executable actions
├── gems/       # Gemini conversational AI assistants
└── skills/     # Cross-platform standardized capabilities
```

## Tool Types

### 🤖 Agents
**→ [agents/](agents/) directory**

Specialized AI entities capable of complex reasoning and multi-step workflows. Agents maintain context and can execute sophisticated analysis within their domain of expertise.

**Use cases:**
- Complex data analysis and investigation
- Multi-step workflow automation
- Domain-specific expertise and guidance
- Research and exploration tasks

### ⚡ Commands
**→ [commands/](commands/) directory**

Atomic, executable actions that provide immediate functionality. Commands are designed for quick, specific tasks and can be invoked directly by AI agents.

**Use cases:**
- Quick utility functions
- Integration with external services
- Automated task execution
- CI/CD pipeline integration

### 💎 Gems
**→ [gems/](gems/) directory**

Conversational AI assistants created within Google's Gemini platform. Each Gem is tailored with specific instructions and knowledge bases for particular domains or tasks.

**Use cases:**
- Specialized conversational interfaces
- Domain-specific assistance
- Template-based content generation
- Interactive workflows

### 🛠️ Skills
**→ [skills/](skills/) directory**

Standardized capabilities that work across multiple AI platforms using the agentskills.io specification. Skills provide reusable functionality with cross-platform compatibility.

**Use cases:**
- Cross-platform tool compatibility
- Standardized automation workflows
- Reusable capability libraries
- Platform-agnostic functionality

## Getting Started

1. **Browse Available Tools**: Check the [root categories.yaml](../categories.yaml) for categorized tools
2. **Explore by Type**: Navigate to the specific tool type directory that matches your needs
3. **Review Documentation**: Each tool type has detailed README files with usage instructions
4. **Choose Your Platform**: Select tools compatible with your AI platform of choice

## Contributing New Tools

1. **Choose the Right Type**: Determine whether your tool is best suited as a Skill, Command, Agent, or Gem
2. **Follow Standards**: Each tool type has specific formatting and structure requirements
3. **Add to Registry**: Tools are automatically categorized in `categories.yaml` or placed in "General" during builds
4. **Test Thoroughly**: Validate your tool works across intended platforms

For detailed contribution guidelines, see the main repository [AGENTS.md](../AGENTS.md) file.

## Tool Registry

All tools in this collection are automatically organized by the build system. Specialized tools are listed in the root `categories.yaml` file, while uncategorized tools are automatically placed in the "General" category for tool discovery and marketplace organization.
