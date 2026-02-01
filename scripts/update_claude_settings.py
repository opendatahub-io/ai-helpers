#!/usr/bin/env python3
"""
Update Claude Code marketplace by scanning tools from categories.yaml configuration.

This script loads the centralized categories.yaml file and generates:
- marketplace.json file with plugin catalog information
- claude-settings.json file with basic configuration
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

try:
    import yaml
except ImportError:
    print(
        "Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr
    )
    sys.exit(1)

# Import duplicate detection function from validate_tools.py
try:
    # Try importing from the same directory (when run from scripts/)
    from validate_tools import get_filesystem_tools_with_duplicates_check
except ImportError:
    try:
        # Try importing with scripts path (when run from repo root)
        scripts_dir = Path(__file__).parent
        sys.path.insert(0, str(scripts_dir))
        from validate_tools import get_filesystem_tools_with_duplicates_check
    except ImportError:
        # If validate_tools.py is not available, fall back to basic duplicate detection
        get_filesystem_tools_with_duplicates_check = None


def load_categories_config(categories_path: Path) -> Dict:
    """Load categories configuration from categories.yaml."""

    if not categories_path.exists():
        print(
            f"Error: Categories configuration not found: {categories_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(categories_path, "r") as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        print(f"Error: Could not read categories configuration: {e}", file=sys.stderr)
        sys.exit(1)


def title_to_slug(title: str) -> str:
    """Convert gem title to slug format (lowercase, spaces/special chars to hyphens)"""
    return re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")


def get_filesystem_tools(helpers_dir: Path) -> Dict[str, str]:
    """Extract all tool names from the filesystem with their types

    Returns:
        Dict mapping tool name to tool type
    """
    # Use the comprehensive duplicate detection function if available
    if get_filesystem_tools_with_duplicates_check is not None:
        filesystem_tools, duplicate_errors = get_filesystem_tools_with_duplicates_check(
            helpers_dir
        )

        # Report duplicate errors
        for error in duplicate_errors:
            print(f"Warning: {error}", file=sys.stderr)

        return filesystem_tools

    # Fallback implementation with basic duplicate detection
    filesystem_tools = {}

    # Skills - directories in helpers/skills/
    skills_dir = helpers_dir / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        for item in skills_dir.iterdir():
            if item.is_dir():
                tool_name = item.name
                if tool_name in filesystem_tools:
                    print(
                        f"Warning: Duplicate tool name '{tool_name}' found - skill ({item}) conflicts with {filesystem_tools[tool_name]}",
                        file=sys.stderr,
                    )
                filesystem_tools[tool_name] = "skill"

    # Commands - .md files in helpers/commands/
    commands_dir = helpers_dir / "commands"
    if commands_dir.exists() and commands_dir.is_dir():
        for item in commands_dir.iterdir():
            if item.is_file() and item.suffix == ".md":
                # Skip README.md files (case-insensitive)
                if item.name.lower() == "readme.md":
                    continue
                tool_name = item.stem
                if tool_name in filesystem_tools:
                    print(
                        f"Warning: Duplicate tool name '{tool_name}' found - command ({item}) conflicts with {filesystem_tools[tool_name]}",
                        file=sys.stderr,
                    )
                filesystem_tools[tool_name] = "command"

    # Agents - .md files in helpers/agents/
    agents_dir = helpers_dir / "agents"
    if agents_dir.exists() and agents_dir.is_dir():
        for item in agents_dir.iterdir():
            if item.is_file() and item.suffix == ".md":
                # Skip README.md files (case-insensitive)
                if item.name.lower() == "readme.md":
                    continue
                tool_name = item.stem
                if tool_name in filesystem_tools:
                    print(
                        f"Warning: Duplicate tool name '{tool_name}' found - agent ({item}) conflicts with {filesystem_tools[tool_name]}",
                        file=sys.stderr,
                    )
                filesystem_tools[tool_name] = "agent"

    # Gems - titles from gems.yaml
    gems_file = helpers_dir / "gems" / "gems.yaml"
    if gems_file.exists() and gems_file.is_file():
        try:
            with open(gems_file, "r", encoding="utf-8") as f:
                gems_data = yaml.safe_load(f)

            if gems_data and "gems" in gems_data:
                for gem in gems_data["gems"]:
                    if "title" in gem:
                        tool_name = title_to_slug(gem["title"])
                        if tool_name in filesystem_tools:
                            print(
                                f"Warning: Duplicate tool name '{tool_name}' found - gem (title: {gem['title']}) conflicts with {filesystem_tools[tool_name]}",
                                file=sys.stderr,
                            )
                        filesystem_tools[tool_name] = "gem"
        except (yaml.YAMLError, IOError) as e:
            print(
                f"Warning: Could not parse gems.yaml ({gems_file}): {e}",
                file=sys.stderr,
            )

    return filesystem_tools


def get_tool_source_path(tool: Dict) -> str:
    """Generate source path for a tool based on its type."""

    # Validate required keys exist and are strings
    tool_type = tool.get("type")
    tool_name = tool.get("name")

    if not isinstance(tool_type, str) or not tool_type:
        print(f"Warning: Tool missing or invalid 'type' key: {tool}", file=sys.stderr)
        return ""

    if not isinstance(tool_name, str) or not tool_name:
        print(f"Warning: Tool missing or invalid 'name' key: {tool}", file=sys.stderr)
        return ""

    if tool_type == "skill":
        return f"./helpers/skills/{tool_name}"
    elif tool_type == "command":
        return f"./helpers/commands/{tool_name}.md"
    elif tool_type == "agent":
        return f"./helpers/agents/{tool_name}.md"
    elif tool_type == "gem":
        # For gems, we don't have a local source file, they're external
        return ""
    else:
        print(
            f"Warning: Unknown tool type '{tool_type}' for tool '{tool_name}'",
            file=sys.stderr,
        )
        return ""


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


def generate_claude_settings(categories_config: Dict) -> Dict:
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

    # Enable the single plugin containing all helpers
    settings["enabledPlugins"]["odh-ai-helpers@odh-ai-helpers"] = True

    return settings


def generate_marketplace_json(
    categories_config: Dict, external_plugins: List[Dict]
) -> Dict:
    """Generate marketplace.json configuration."""

    # Base marketplace structure
    marketplace = {
        "name": "odh-ai-helpers",
        "owner": {"name": "ODH"},
        "plugins": [],
    }

    # Add external plugins first
    marketplace["plugins"].extend(external_plugins)

    # Add single plugin entry for all helpers
    marketplace["plugins"].append(
        {
            "name": "odh-ai-helpers",
            "source": "./helpers",
            "description": "AI automation tools, plugins, and assistants for enhanced productivity",
            "strict": False,
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

    categories_path = repo_root / "categories.yaml"
    settings_path = repo_root / "images" / "claude" / "claude-settings.json"
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    external_sources_path = repo_root / "claude-external-plugin-sources.json"

    print("Loading categories configuration...")
    categories_config = (
        load_categories_config(categories_path) if categories_path.exists() else {}
    )

    if not isinstance(categories_config, dict):
        print(
            "Error: categories.yaml must contain a dictionary with categories",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get filesystem tools to infer types
    helpers_dir = repo_root / "helpers"
    filesystem_tools = get_filesystem_tools(helpers_dir)

    # Flatten tools from all categories and count by type
    all_tools = []
    tool_counts = {}
    categorized_tools = set()

    # Process tools from explicit categories
    for category_name, tools in categories_config.items():
        if not isinstance(tools, list):
            print(
                f"Warning: Category '{category_name}' does not contain a list",
                file=sys.stderr,
            )
            continue

        for tool_name in tools:
            if not isinstance(tool_name, str):
                print(
                    f"Warning: Tool name must be a string in category '{category_name}': {tool_name}",
                    file=sys.stderr,
                )
                continue

            # Get tool type from filesystem
            if tool_name in filesystem_tools:
                tool_type = filesystem_tools[tool_name]
                tool_dict = {"name": tool_name, "type": tool_type}
                all_tools.append(tool_dict)
                tool_counts[tool_type] = tool_counts.get(tool_type, 0) + 1
                categorized_tools.add(tool_name)
            else:
                print(
                    f"Warning: Tool '{tool_name}' not found in filesystem",
                    file=sys.stderr,
                )

    # Process uncategorized tools (automatically add to "General" category)
    uncategorized_tools = []
    for tool_name, tool_type in filesystem_tools.items():
        if tool_name not in categorized_tools:
            tool_dict = {"name": tool_name, "type": tool_type}
            all_tools.append(tool_dict)
            tool_counts[tool_type] = tool_counts.get(tool_type, 0) + 1
            uncategorized_tools.append(tool_name)

    if uncategorized_tools:
        print(
            f"Note: Found {len(uncategorized_tools)} uncategorized tools (will be placed in General category): {', '.join(uncategorized_tools)}"
        )

    print("Found tools:")
    for tool_type, count in sorted(tool_counts.items()):
        tools_of_type = [
            t.get("name", "unknown")
            for t in all_tools
            if t.get("type") == tool_type and isinstance(t.get("name"), str)
        ]
        print(f"  {tool_type}: {count} ({', '.join(tools_of_type)})")

    # Load external plugins
    external_plugins = load_external_plugins(external_sources_path)
    if external_plugins:
        ext_names = [
            plugin.get("name", "unknown")
            for plugin in external_plugins
            if isinstance(plugin.get("name"), str)
        ]
        print(f"Found external plugins: {', '.join(ext_names)}")

    print("Generating Claude settings...")
    settings = generate_claude_settings(categories_config)

    print(f"Writing {settings_path}...")
    write_settings_file(settings_path, settings)

    print("Generating marketplace configuration...")
    marketplace = generate_marketplace_json(categories_config, external_plugins)

    print(f"Writing {marketplace_path}...")
    write_settings_file(marketplace_path, marketplace)

    print("✓ Claude settings and marketplace updated successfully!")


if __name__ == "__main__":
    main()
