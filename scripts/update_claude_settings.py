#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pyyaml"]
# ///
"""
Generate the Claude Code marketplace and container settings from plugins/.

Each plugins/<plugin>/ directory with a .claude-plugin/plugin.json becomes a
marketplace plugin entry (source ./plugins/<plugin>). External plugins are read
from claude-external-plugin-sources.json. The container claude-settings.json
enables the individual odh-* plugins (not the deprecated odh-ai-helpers
umbrella, which re-exports the same skills via symlinks).
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Import duplicate detection from validate_tools (best-effort).
try:
    from validate_tools import get_plugin_tools
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from validate_tools import get_plugin_tools
    except ImportError:
        get_plugin_tools = None

MARKETPLACE_NAME = "odh-ai-helpers"
UMBRELLA_PLUGIN = "odh-ai-helpers"


def load_local_plugins(plugins_dir: Path) -> List[Dict]:
    """Discover local plugins from plugins/<plugin>/.claude-plugin/plugin.json."""
    if not plugins_dir.is_dir():
        print(f"Error: plugins directory not found: {plugins_dir}", file=sys.stderr)
        sys.exit(1)

    plugins: List[Dict] = []
    for plugin_dir in sorted(p for p in plugins_dir.iterdir() if p.is_dir()):
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            print(
                f"Warning: {plugin_dir.name} has no .claude-plugin/plugin.json, skipping",
                file=sys.stderr,
            )
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"Warning: invalid plugin.json in {plugin_dir.name}: {e}", file=sys.stderr)
            continue
        plugins.append(
            {
                "name": data.get("name", plugin_dir.name),
                "source": f"./plugins/{plugin_dir.name}",
                "description": data.get("description", ""),
            }
        )
    return plugins


def load_external_plugins(config_path: Path) -> List[Dict]:
    """Load external plugin definitions (source specified inline)."""
    if not config_path.exists():
        return []
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: could not read external plugins config: {e}", file=sys.stderr)
        return []

    external: List[Dict] = []
    for plugin in config.get("plugins", []):
        if "name" not in plugin or "source" not in plugin:
            print(f"Warning: skipping malformed external plugin: {plugin}", file=sys.stderr)
            continue
        external.append(
            {
                "name": plugin["name"],
                "description": plugin.get("description", f"{plugin['name']} plugin"),
                "source": plugin["source"],
            }
        )
    return external


def generate_marketplace(local: List[Dict], external: List[Dict]) -> Dict:
    """Build marketplace.json: external plugins first, then local plugins."""
    plugins: List[Dict] = list(external)
    for p in local:
        plugins.append({"name": p["name"], "source": p["source"], "description": p["description"]})
    return {"name": MARKETPLACE_NAME, "owner": {"name": "ODH"}, "plugins": plugins}


def generate_settings(local: List[Dict], external: List[Dict]) -> Dict:
    """Container settings: enable individual odh-* plugins + external plugins."""
    settings = {
        "extraKnownMarketplaces": {
            MARKETPLACE_NAME: {"source": {"source": "directory", "path": "/opt/ai-helpers"}}
        },
        "enabledPlugins": {},
    }
    for p in local:
        if p["name"] == UMBRELLA_PLUGIN:
            # Deprecated backwards-compat bundle; not enabled by default.
            continue
        settings["enabledPlugins"][f"{MARKETPLACE_NAME}@{p['name']}"] = True
    for p in external:
        settings["enabledPlugins"][f"{MARKETPLACE_NAME}@{p['name']}"] = True
    return settings


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main() -> None:
    repo_root = Path(__file__).parent.parent
    plugins_dir = repo_root / "plugins"
    external_path = repo_root / "claude-external-plugin-sources.json"
    settings_path = repo_root / "images" / "claude" / "claude-settings.json"
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"

    local = load_local_plugins(plugins_dir)
    external = load_external_plugins(external_path)

    print(f"Found {len(local)} local plugin(s): {', '.join(p['name'] for p in local)}")
    if external:
        print(f"Found {len(external)} external plugin(s): {', '.join(p['name'] for p in external)}")

    # Best-effort duplicate detection across non-umbrella plugins.
    if get_plugin_tools is not None:
        _, dup_errors = get_plugin_tools(plugins_dir)
        for err in dup_errors:
            print(f"Warning: {err}", file=sys.stderr)

    write_json(settings_path, generate_settings(local, external))
    print(f"Wrote {settings_path}")
    write_json(marketplace_path, generate_marketplace(local, external))
    print(f"Wrote {marketplace_path}")
    print("✓ marketplace and settings updated")


if __name__ == "__main__":
    main()
