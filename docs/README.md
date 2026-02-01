# AI Helpers Website

This directory contains the Github Pages website for the ODH ai-helpers project.

## Structure

- `index.html` - Main website with plugin browser
- `data.json` - Plugin and command metadata (generated)
- `.nojekyll` - Tells Github Pages not to use Jekyll processing

## Building

The website data is generated from the repository structure:

```bash
python3 scripts/build-website.py
# Execute from repo root; also executed when you run `make build`
```

This extracts information from:
- `categories.yaml` - Centralized category registry
- `helpers/commands/*.md` - Command definitions
- `helpers/skills/*/SKILL.md` - Skill definitions
- `helpers/agents/*.md` - Agent definitions
- `helpers/gems/gems.yaml` - Gemini Gems definitions

## Local Development

To test the website locally:

```bash
make docs
# Execute from repo root; visit http://localhost:8000
```

## Deployment

The website is automatically deployed via Github Pages from the `docs/` directory.

The site will be available at: `https://opendatahub-io.github.io/ai-helpers/`

## Updating

When plugins or commands are added/modified:

1. Run `python3 scripts/build-website.py` to regenerate `data.json`
2. Commit both `data.json` and any changes
3. Push to trigger Github Pages rebuild
