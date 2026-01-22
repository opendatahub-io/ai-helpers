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

## Tools Development

This repository is made for collaboration. We highly welcome contributions.

For skills, check out the `helpers/skills/` directory for examples.
For commands, check the `helpers/commands/` directory, and for agents see the `helpers/agents/` directory.
Using AI code assistant itself to develop the tools is highly encouraged.

### Adding New Tools

When contributing new tools:

1. **Skills**: Add to the `helpers/skills/` directory following the agentskills.io format
2. **Commands**: Add to the `helpers/commands/` directory as Markdown files
3. **Agents**: Add to the `helpers/agents/` directory with appropriate documentation
4. **Gemini Gems**: Add to the `helpers/gems/` directory

Once you have added the tool, you'd have to run have to run `make update` in order to generate the website data.
Then you should git commit your change and after than running `make lint` would run local tests to validate the syntax.

### Testing a plugin locally (example with Claude Code)

1. Open `claude`
2. Run `/plugin marketplace add ./`
3. Run `/plugin` then install the local plugin
4. Test plugin and remove local marketplace after done testing which will remove plugin
5. You can now reinstall from the git marketplace

## Tool Registry

The AI Helpers marketplace uses a centralized category registry in `categories.yaml` to organize specialized tools by category. **Tools not listed in any category are automatically placed in the "General" category** - perfect for most contributions!

### Category Registry Structure

Specialized tool categories are registered in `categories.yaml`:

```yaml
CategoryName:
  - specialized-tool
  - another-tool

AnotherCategory:
  - domain-specific-tool
```

### Adding a New Category

To add a new category, edit `categories.yaml` to include the new category as a top-level key:

1. **Add category with tools**:
   ```yaml
   YourCategory:
     - your-tool-name
     - another-tool
   ```

2. **Update documentation**: Run `make update` to regenerate the website

### Automatic Management

The build system automatically handles tool organization and validation:
- Tools not in `categories.yaml` are automatically assigned to "General" category
- Tool types are inferred from filesystem structure
- Duplicate tool names across categories are prevented
- All tools require valid names and types


## Using with Claude Code

Claude Code Marketplace extends Claude's functionality with custom commands, agents, and skills for specific workflows and
tasks.
They enable you to automate repetitive development activities, integrate with tools, and create specialized AI
assistants tailored to your needs.

For comprehensive information about plugin architecture and development, see
the [official Claude Code plugins documentation](https://docs.claude.com/en/docs/claude-code/plugins-reference).

### Install the tools from the Marketplace

1. **Add the marketplace:**
   ```bash
   /plugin marketplace add opendatahub-io/ai-helpers
   ```


2. **Install a plugin:**
   ```bash
   /plugin install odh-ai-helpers
   ```

> [!TIP]
> To browse and install multiple plugins interactively, use `/plugin` after adding the marketplace.
> This will show you all available plugins and allow you to install them selectively.
> For a complete list of all available tools, see **[categories.yaml](categories.yaml)** or visit our [website](https://opendatahub-io.github.io/ai-helpers/).

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
  --pull newer \
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
    --pull newer \
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

## Gemini Gems

The `helpers/gems/` directory contains a curated collection of Gemini Gems - specialized AI assistants for various
development tasks. These can be accessed directly through Google's Gemini platform.

For detailed information about using and contributing Gemini Gems, see [helpers/gems/README.md](helpers/gems/README.md).

## Validating Tools

This repository uses [claudelint](https://github.com/stbenjam/claudelint) to validate the Claude plugin structure:

```bash
make lint
```

## Ethical Guidelines

We must NEVER reference real people by name, even as stylistic examples (e.g., "in the
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

This automatically scans all tools and regenerates the complete documentation and website data.

## License

See [LICENSE](LICENSE) for details.
