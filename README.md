# AI Helpers

This repository is a collaborative place hosting collections of AI plugins to automate and assist with various tasks .

> [!NOTE]
> Right now the focus is to support Claude Code and Cursor AI.
> Other tools are welcome here, please submit Pull Requests.

> [!NOTE]
> This project was inspired by the [OpenShift AI helpers](https://github.com/openshift-eng/ai-helpers).

## Claude Code Plugins

Claude Code plugins extend Claude's functionality with custom commands, subagents and skills for specific workflows and tasks.
They enable you to automate repetitive development activities, integrate with tools, and create specialized AI assistants tailored to your needs.

For comprehensive information about plugin architecture and development, see the [official Claude Code plugins documentation](https://docs.claude.com/en/docs/claude-code/plugins-reference).

### Install the plugins from the Marketplace

1. **Add the marketplace:**
   ```bash
   /plugin marketplace add opendatahub-io/ai-helpers
   ```
> [!IMPORTANT]
> Changes take effect the next time you start Claude Code. If Claude Code is already running, restart it to load the updates.

2. **Install a plugin:**
   ```bash
   /plugin install hello-world@odh-ai-helpers
   ```

> [!TIP]
> To browse and install multiple plugins interactively, use `/plugin` after adding the marketplace.
> This will show you all available plugins and allow you to install them selectively.
> For a complete list of all available plugins, see **[TOOLS.md](TOOLS.md)**.

3. **Use the commands:**
   ```bash
   /hello-world:echo Hello from OpenDataHub!
   ```

### Running Claude Code in a container

A container is available with Claude Code and all plugins pre-installed.

You can build it yourself:
```bash
podman build -f images/claude/Containerfile -t ai-helpers .
```

or you can use the one built by our CI periodically.

To use Claude Code with Google Cloud's Vertex AI, you need to pass through your gcloud credentials and set the required environment variables:

```bash
podman run -it \
  --pull always \
  --userns=keep-id \
  -e CLAUDE_CODE_USE_VERTEX=1 \
  -e CLOUD_ML_REGION=your-ml-region \
  -e ANTHROPIC_VERTEX_PROJECT_ID=your-project-id \
  -e DISABLE_AUTOUPDATER=1 \
  -v ~/.config/gcloud:/home/claude/.config/gcloud:ro,z \
  -v $(pwd):/workspace:z \
  -w /workspace \
  --name claude_code \
  ghcr.io/opendatahub-io/ai-helpers:latest
```

**Environment Variables:**
- `CLAUDE_CODE_USE_VERTEX=1` - Enable Vertex AI integration
- `CLOUD_ML_REGION` - Your GCP region (e.g., `us-east5`)
- `ANTHROPIC_VERTEX_PROJECT_ID` - Your GCP project ID

**Rootless Podman:**
- `--userns=keep-id` - Preserves host user ID mapping, required for the claude user to access mounted volumes

**Volume Mounts:**
- `-v ~/.config/gcloud:/home/claude/.config/gcloud:ro,z` - Passes through your gcloud authentication (read-only with SELinux labeling)
- `-v $(pwd):/workspace:z` - Mounts your current directory into the container

### Running Commands Non-Interactively

You can execute Claude Code commands directly without entering an interactive session using the `-p` or `--print` flag:

```bash
podman run -it \
  --pull always \
  --userns=keep-id \
  -e CLAUDE_CODE_USE_VERTEX=1 \
  -e CLOUD_ML_REGION=your-ml-region \
  -e ANTHROPIC_VERTEX_PROJECT_ID=your-project-id \
  -v ~/.config/gcloud:/home/claude/.config/gcloud:ro,z \
  -v $(pwd):/workspace:z \
  -w /workspace \
  --name claude_code \
  ghcr.io/opendatahub-io/ai-helpers:latest \
  --print "/hello-world:echo Hello from Claude Code!"
```

This will:
1. Start the container with your gcloud credentials
2. Execute the `/hello-world:echo` command with the provided message
3. Print the response and exit when complete

### Plugin Development

This repository is made for collaboration. We highly welcome contributions.

For Claude plugins, check out the `claude-plugins/` directory for examples.
Make sure your commands and agents follow the conventions for the Sections structure presented in the hello-world reference implementation plugin (see [`hello-world:echo`](claude-plugins/hello-world/commands/echo.md) for an example). Using Claude Code itself to develop the plugins is highly encouraged.

### Adding New Commands

When contributing new commands:

1. **If your command fits an existing plugin**: Add it to the appropriate plugin's `commands/` directory
2. **If your command doesn't have a clear parent plugin**: Add it to the **utils plugin** (`claude-plugins/utils/commands/`)
   - The utils plugin serves as a catch-all for commands that don't fit existing categories
   - Once we accumulate several related commands in utils, they can be segregated into a new targeted plugin

### Creating a New Plugin

For detailed Claude Code development instructions, see [claude-plugins/README.md](claude-plugins/README.md).

## Categorization System

The AI Helpers marketplace uses a categorization system to organize tools by their intended purpose and workflows. Categories are defined in `categories.json` and automatically applied to tools in the website interface.

### Available Categories

- **General**: Default category for general-purpose tools and utilities
- **AIPCC**: Tools specifically designed for AIPCC workflows and processes

### How Categorization Works

Categories are configured in the `categories.json` file at the repository root. Each category defines:
- `name`: Display name for the category
- `description`: Brief description of the category's purpose
- `claude_plugin_dirs`: List of Claude Code plugin directory names that belong to this category
- `cursor_commands`: List of Cursor command names that belong to this category

Example category definition:
```json
{
  "categories": {
    "general": {
      "name": "General",
      "description": "General-purpose tools and utilities",
      "claude_plugin_dirs": ["git", "utils", "python-packaging"],
      "cursor_commands": ["jira-sprint-summary"]
    }
  }
}
```

### Adding a New Category

To add a new category:

1. **Edit `categories.json`**: Add your new category definition
   ```json
   "your-category": {
     "name": "Your Category Name",
     "description": "Description of your category's purpose",
     "claude_plugin_dirs": ["plugin1", "plugin2"],
     "cursor_commands": ["command1", "command2"]
   }
   ```

2. **Assign tools to the category**:
   - For Claude Code plugins: Add the plugin directory name to `claude_plugin_dirs`
   - For Cursor commands: Add the command name (without .md extension) to `cursor_commands`
   - For Gemini Gems: Categories are automatically applied based on YAML metadata

3. **Update documentation**: Run `make update` to regenerate the website data

### Automatic Categorization

The build system automatically:
- Assigns uncategorized tools to the "general" category
- Updates `categories.json` during `make update` to include any new tools
- Preserves manual categorizations while ensuring no tools are left uncategorized

This ensures zero maintenance burden for new tools while preserving intentional categorizations.

## Cursor

The `cursor/` directory contains custom commands and functionalities specifically designed for Cursor AI integration.
When possible, the commands are shared with Claude Code to avoid duplication.

For detailed documentation on Cursor AI helpers, see [cursor/README.md](cursor/README.md).

## Gemini Gems

The `gemini-gems/` directory contains a curated collection of Gemini Gems - specialized AI assistants for various development tasks. These can be accessed directly through Google's Gemini platform.

For detailed information about using and contributing Gemini Gems, see [gemini-gems/README.md](gemini-gems/README.md).

## Validating Plugins

This repository uses [claudelint](https://github.com/stbenjam/claudelint) to validate the Claude plugin structure:

```bash
make lint
```

## Updating Plugin Documentation

After adding or modifying plugins, regenerate the TOOLS.md file:

```bash
make update
```

## Ethical Guidelines

Plugins, commands, skills, and hooks must NEVER reference real people by name, even as stylistic examples (e.g., "in the style of 'specific human'").

**Ethical rationale:**
1. **Consent**: Individuals have not consented to have their identity or persona used in AI-generated content
2. **Misrepresentation**: AI cannot accurately replicate a person's unique voice, style, or intent
3. **Intellectual Property**: A person's distinctive style may be protected
4. **Dignity**: Using someone's identity without permission diminishes their autonomy

**Instead, describe specific qualities explicitly**

Good examples:

* "Write commit messages that are direct, technically precise, and focused on the rationale behind changes"
* "Explain using clear analogies, a sense of wonder, and accessible language for non-experts"
* "Code review comments that are encouraging, constructive, and focus on collaborative improvement"

When you identify a desirable characteristic (clarity, brevity, formality, humor, etc.), describe it explicitly rather than using a person as proxy.

## Pre-commit Hooks (Optional)

For additional validation, the repository includes `.pre-commit-config.yaml` with Red Hat security and AI-readiness hooks:

```bash
pre-commit install
pre-commit install --hook-type pre-push
pre-commit run --all-files  # Test all files
```

This automatically scans all plugins and regenerates the complete plugin/command documentation in TOOLS.md.

## License

See [LICENSE](LICENSE) for details.
