# AI Helpers

This repository is a collaborative place hosting collections of AI plugins to automate and assist with various tasks.

> [!NOTE]
> Right now the focus is to support Claude Code, Gemini Gems, and Cursor AI.
> Other tools are welcome here, please submit Pull Requests.

> [!NOTE]
> This project was inspired by the [OpenShift AI helpers](https://github.com/openshift-eng/ai-helpers).

## Got an Idea?

Have an idea for a new plugin, command, or assistant but not sure how to implement it? We'd love to hear about it!
Simply file a GitHub issue with your idea in the title and we'll work together to make it happen.

> [!TIP]
> [Share your idea](https://github.com/opendatahub-io/ai-helpers/issues/new?assignees=&labels=enhancement%2Chelp+wanted%2Cidea&template=07_idea_request.md&title=%5BIdea%5D+)

No implementation details needed - just describe what you'd like to automate or what workflow you think could be
improved. The community can help figure out the best way to build it.

## Claude Code Plugins

Claude Code plugins extend Claude's functionality with custom commands, subagents, and skills for specific workflows and
tasks.
They enable you to automate repetitive development activities, integrate with tools, and create specialized AI
assistants tailored to your needs.

For comprehensive information about plugin architecture and development, see
the [official Claude Code plugins documentation](https://docs.claude.com/en/docs/claude-code/plugins-reference).

### Install the plugins from the Marketplace

1. **Add the marketplace:**
   ```bash
   /plugin marketplace add opendatahub-io/ai-helpers
   ```


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

### Running Claude Code in a Container

A container image is available with Claude Code and all plugins pre-installed:
`ghcr.io/opendatahub-io/ai-helpers:latest`

You can also build it yourself by running:

```bash
podman build -f images/claude/Containerfile -t ai-helpers .
```

To use Claude Code with Google Cloud's Vertex AI, you need to pass through your gcloud credentials and set the required
environment variables:

```bash
podman run -it --rm \
  --pull always \
  --userns=keep-id \
  -e CLAUDE_CODE_USE_VERTEX=1 \
  -e CLOUD_ML_REGION=your-ml-region \
  -e ANTHROPIC_VERTEX_PROJECT_ID=your-project-id \
  -e DISABLE_AUTOUPDATER=1 \
  -v ~/.config/gcloud:/home/claude/.config/gcloud:ro,z \
  -v ~/.claude:/home/claude/.claude:z \
  -v ~/.claude.json:/home/claude/.claude.json:z \
  -v $(pwd):$(pwd):z \
  -w $(pwd) \
  ghcr.io/opendatahub-io/ai-helpers:latest
```

You can execute Claude Code commands directly without entering an interactive session using the `-p` or `--print` flag.

**Environment Variables:**

- `CLAUDE_CODE_USE_VERTEX=1` - Enable Vertex AI integration
- `CLOUD_ML_REGION` - Your GCP region (e.g., `us-east5`)
- `ANTHROPIC_VERTEX_PROJECT_ID` - Your GCP project ID

**Rootless Podman:**

- `--userns=keep-id` - Preserves host user ID mapping, required for the claude user to access mounted volumes

**Volume Mounts:**

- `-v ~/.claude:/home/claude/.claude:z` - Mounts your local Claude sessions and project data
- `-v ~/.claude.json:/home/claude/.claude.json:z` - Mounts your user configuration (onboarding state, preferences)
- `-v $(pwd):$(pwd):z` - Mounts the project at the same absolute path as on the host to reuse Claude's session data
- `-w $(pwd)` - Sets the working directory to match the host path

Add this to your `~/.bashrc` for easy launching of the container:

```bash
claude-container() {
  podman run -it --rm \
    --pull always \
    --userns=keep-id \
    -e CLAUDE_CODE_USE_VERTEX=1 \
    -e CLOUD_ML_REGION="${CLOUD_ML_REGION}" \
    -e ANTHROPIC_VERTEX_PROJECT_ID="${ANTHROPIC_VERTEX_PROJECT_ID}" \
    -e DISABLE_AUTOUPDATER=1 \
    -v ~/.config/gcloud:/home/claude/.config/gcloud:ro,z \
    -v ~/.claude:/home/claude/.claude:z \
    -v ~/.claude.json:/home/claude/.claude.json:z \
    -v "$(pwd):$(pwd):z" \
    -w "$(pwd)" \
    ghcr.io/opendatahub-io/ai-helpers:latest "$@"
}
```

### Plugin Development

This repository is made for collaboration. We highly welcome contributions.

For Claude plugins, check out the `claude-plugins/` directory for examples.
Make sure your commands and agents follow the conventions for the Sections structure presented in the hello-world
reference implementation plugin (see [`hello-world:echo`](claude-plugins/hello-world/commands/echo.md) for an example).
Using Claude Code itself to develop the plugins is highly encouraged.

### Adding local plugin to session to be able to test

1. Open `claude`
2. Run `/plugin marketplace add ./`
3. Run `/plugin` then install the local plugin
4. Test plugin and remove local marketplace after done testing which will remove plugin
5. You can now reinstall from the git marketplace

### Adding New Commands

When contributing new commands:

1. **If your command fits an existing plugin**: Add it to the appropriate plugin's `commands/` directory
2. **If your command doesn't have a clear parent plugin**: Add it to the **utils plugin** (
   `claude-plugins/utils/commands/`)
    - The utils plugin serves as a catch-all for commands that don't fit existing categories
    - Once we accumulate several related commands in utils, they can be segregated into a new targeted plugin

### Creating a New Plugin

For detailed Claude Code development instructions, see [claude-plugins/README.md](claude-plugins/README.md).

## Categorization System

The AI Helpers marketplace uses a categorization system to organize tools by their intended purpose and workflows.
Categories are defined in `categories.json` and automatically applied to tools in the website interface.

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
      "claude_plugin_dirs": [
        "git",
        "utils",
        "python-packaging"
      ],
      "cursor_commands": [
        "jira-sprint-summary"
      ],
      "gemini_gems": [
        "Email Copilot",
        "Technical Spike & Investigation"
      ]
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
     "cursor_commands": ["command1", "command2"],
     "gemini_gems": ["gem title", "gem title 2"]
   }
   ```

2. **Assign tools to the category**:
    - For Claude Code plugins: Add the plugin directory name to `claude_plugin_dirs`
    - For Cursor commands: Add the command name (without .md extension) to `cursor_commands`
    - For Gemini Gems: Add the gem title to `gemini_gems`

3. **Update documentation**: Run `make update` to regenerate the website data

### Automatic Categorization

The build system automatically:

- Assigns uncategorized tools to the "general" category
- Updates `categories.json` during `make update` to include any new tools
- Preserves manual categorizations while ensuring no tools are left uncategorized

This ensures zero maintenance burden for new tools while preserving intentional categorization.

## Cursor

The `cursor/` directory contains custom commands and functionalities specifically designed for Cursor AI integration.
When possible, the commands are shared with Claude Code to avoid duplication.

For detailed documentation on Cursor AI helpers, see [cursor/README.md](cursor/README.md).

## Gemini Gems

The `gemini-gems/` directory contains a curated collection of Gemini Gems - specialized AI assistants for various
development tasks. These can be accessed directly through Google's Gemini platform.

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

Plugins, commands, skills, and hooks must NEVER reference real people by name, even as stylistic examples (e.g., "in the
style of 'specific human'").

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

When you identify a desirable characteristic (clarity, brevity, formality, humor, etc.), describe it explicitly rather
than using a person as proxy.

## Pre-commit Hooks (Optional)

For additional validation, the repository includes `.pre-commit-config.yaml` with Red Hat security and AI-readiness
hooks:

```bash
pre-commit install
pre-commit install --hook-type pre-push
pre-commit run --all-files  # Test all files
```

This automatically scans all plugins and regenerates the complete plugin/command documentation in [TOOLS.md](TOOLS.md).

## License

See [LICENSE](LICENSE) for details.
