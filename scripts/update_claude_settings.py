#!/usr/bin/env python3
"""
Update Claude Code settings and marketplace by scanning all plugins in the repository.

This script scans the plugins directory, reads plugin metadata from plugin.json files,
and generates both:
- claude-settings.json file with all available plugins enabled
- marketplace.json file with plugin catalog information
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def get_plugin_metadata(plugins_dir: Path) -> List[Dict]:
    """Extract plugin metadata from plugin.json files."""

    plugin_metadata = []

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue

        # Read plugin metadata
        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if not plugin_json_path.exists():
            continue

        try:
            with open(plugin_json_path, "r") as f:
                plugin_data = json.load(f)

            plugin_name = plugin_data.get("name", plugin_dir.name)
            plugin_description = plugin_data.get("description", f"{plugin_name} plugin")
            plugin_source = f"./claude-plugins/{plugin_dir.name}"

            plugin_metadata.append(
                {
                    "name": plugin_name,
                    "description": plugin_description,
                    "source": plugin_source,
                }
            )

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read {plugin_json_path}: {e}", file=sys.stderr)
            continue

    return plugin_metadata


def load_external_plugins(config_path: Path) -> List[Dict]:
    """Load external plugin definitions from config file.

    External plugins are specified with their source (github, git URL, etc.)
    and are included directly in the marketplace without cloning.
    """
    if not config_path.exists():
        return []

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read external plugins config: {e}", file=sys.stderr)
        return []

    external_plugins = []
    for plugin in config.get("plugins", []):
        # Validate required fields
        if "name" not in plugin:
            print(
                f"Warning: Skipping external plugin missing 'name': {plugin}",
                file=sys.stderr,
            )
            continue
        if "source" not in plugin:
            print(
                f"Warning: Skipping external plugin '{plugin.get('name')}' missing 'source'",
                file=sys.stderr,
            )
            continue

        external_plugins.append(
            {
                "name": plugin["name"],
                "description": plugin.get("description", f"{plugin['name']} plugin"),
                "source": plugin["source"],
            }
        )

    return external_plugins


def merge_plugins(
    local_plugins: List[Dict], external_plugins: List[Dict]
) -> List[Dict]:
    """Merge local and external plugins, warning on name conflicts.

    Local plugins take precedence over external plugins with the same name.
    """
    local_names = {p["name"] for p in local_plugins}
    merged = list(local_plugins)

    for plugin in external_plugins:
        if plugin["name"] in local_names:
            print(
                f"Warning: External plugin '{plugin['name']}' conflicts with "
                f"local plugin, skipping external",
                file=sys.stderr,
            )
            continue
        merged.append(plugin)

    return merged


def generate_claude_settings(plugin_metadata: List[Dict]) -> Dict:
    """Generate Claude Code settings configuration."""

    # Base configuration
    settings = {
        "extraKnownMarketplaces": {
            "odh-ai-helpers": {
                "source": {"source": "directory", "path": "/opt/ai-helpers"}
            }
        },
        "enabledPlugins": {},
    }

    # Add all discovered plugins to enabledPlugins
    for plugin in plugin_metadata:
        plugin_name = plugin["name"]
        settings["enabledPlugins"][f"{plugin_name}@odh-ai-helpers"] = True

    return settings


def generate_marketplace_json(plugin_metadata: List[Dict]) -> Dict:
    """Generate marketplace.json configuration."""

    # Base marketplace structure
    marketplace = {
        "name": "odh-ai-helpers",
        "owner": {"name": "ODH"},
        "plugins": [],
    }

    # Add all discovered plugins to the marketplace
    for plugin in plugin_metadata:
        marketplace["plugins"].append(
            {
                "name": plugin["name"],
                "source": plugin["source"],
                "description": plugin["description"],
            }
        )

    return marketplace


def write_settings_file(settings_path: Path, settings: Dict) -> None:
    """Write the claude-settings.json file."""

    # Ensure the directory exists
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with proper formatting
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")  # Add final newline


def main():
    """Main entry point."""

    # Determine repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    plugins_dir = repo_root / "claude-plugins"
    settings_path = repo_root / "images" / "claude" / "claude-settings.json"
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    external_sources_path = repo_root / "claude-external-plugin-sources.json"

    if not plugins_dir.exists():
        print(f"Error: Plugins directory not found: {plugins_dir}", file=sys.stderr)
        sys.exit(1)

    print("Scanning local plugins...")
    local_plugins = get_plugin_metadata(plugins_dir)

    if not local_plugins:
        print("Warning: No local plugins found", file=sys.stderr)
    else:
        plugin_names = [plugin["name"] for plugin in local_plugins]
        print(f"Found local plugins: {', '.join(plugin_names)}")

    # Load and merge external plugins
    external_plugins = load_external_plugins(external_sources_path)
    if external_plugins:
        ext_names = [plugin["name"] for plugin in external_plugins]
        print(f"Found external plugins: {', '.join(ext_names)}")

    all_plugins = merge_plugins(local_plugins, external_plugins)

    print("Generating Claude settings...")
    settings = generate_claude_settings(all_plugins)

    print(f"Writing {settings_path}...")
    write_settings_file(settings_path, settings)

    print("Generating marketplace configuration...")
    marketplace = generate_marketplace_json(all_plugins)

    print(f"Writing {marketplace_path}...")
    write_settings_file(marketplace_path, marketplace)

    print("✓ Claude settings and marketplace updated successfully!")


if __name__ == "__main__":
    main()
