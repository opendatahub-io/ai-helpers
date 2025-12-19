#!/usr/bin/env python3
"""
Build website data for ODH ai-helpers Github Pages
Extracts plugin and command information from the repository
"""

import json
import re
import yaml
from pathlib import Path
from typing import Dict, List


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Extract frontmatter from markdown file"""
    frontmatter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 2:
            fm_lines = parts[1].strip().split("\n")
            for line in fm_lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
    return frontmatter


def extract_synopsis(content: str) -> str:
    """Extract synopsis from command markdown"""
    match = re.search(r"## Synopsis\s*```\s*([^\n]+)", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def get_plugin_commands(
    plugin_path: Path, plugin_name: str = ""
) -> List[Dict[str, str]]:
    """Get all commands for a plugin"""
    commands = []
    commands_dir = plugin_path / "commands"

    if not commands_dir.exists():
        return commands

    for cmd_file in sorted(commands_dir.glob("*.md")):
        try:
            content = cmd_file.read_text()
            frontmatter = parse_frontmatter(content)
            synopsis = extract_synopsis(content)

            command_name = cmd_file.stem

            # Fix synopsis to use proper Claude Code format: /plugin:command
            if synopsis and plugin_name:
                # Replace the command part with the plugin:command format
                # E.g., "/sprint-summary <args>" becomes "/jira:sprint-summary <args>"
                synopsis = synopsis.replace(
                    f"/{command_name}", f"/{plugin_name}:{command_name}"
                )

            # Create relative path from repository root for GitHub link
            base_path = cmd_file.parents[
                3
            ]  # Get repo root (three levels up from claude-plugins/plugin/commands)
            relative_path = cmd_file.relative_to(base_path)

            commands.append(
                {
                    "name": command_name,
                    "description": frontmatter.get("description", ""),
                    "synopsis": synopsis,
                    "argument_hint": frontmatter.get("argument-hint", ""),
                    "file_path": str(relative_path),
                }
            )
        except Exception as e:
            print(f"Error processing {cmd_file}: {e}")

    return commands


def get_plugin_skills(plugin_path: Path) -> List[Dict[str, str]]:
    """Get all skills for a plugin"""
    skills = []
    skills_dir = plugin_path / "skills"

    if not skills_dir.exists():
        return skills

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        try:
            content = skill_file.read_text()
            frontmatter = parse_frontmatter(content)

            skill_name = skill_dir.name
            # Create relative path from repository root for GitHub link
            base_path = skill_file.parents[
                4
            ]  # Get repo root (four levels up from claude-plugins/plugin/skills/skill/SKILL.md)
            relative_path = skill_file.relative_to(base_path)

            skills.append(
                {
                    "name": frontmatter.get("name", skill_name),
                    "id": skill_name,
                    "description": frontmatter.get("description", ""),
                    "file_path": str(relative_path),
                }
            )
        except Exception as e:
            print(f"Error processing {skill_file}: {e}")

    return skills


def get_plugin_hooks(plugin_path: Path) -> List[Dict[str, str]]:
    """Get all hooks for a plugin"""
    hooks = []
    hooks_file = plugin_path / "hooks" / "hooks.json"

    if not hooks_file.exists():
        return hooks

    try:
        with open(hooks_file) as f:
            hooks_data = json.load(f)

        # Extract description and hook types
        description = hooks_data.get("description", "")
        hook_types = hooks_data.get("hooks", {})

        for hook_type, hook_configs in hook_types.items():
            hooks.append(
                {"name": hook_type, "description": description, "type": hook_type}
            )
    except Exception as e:
        print(f"Error processing {hooks_file}: {e}")

    return hooks


def get_plugin_agents(plugin_path: Path) -> List[Dict[str, str]]:
    """Get all agents for a plugin"""
    agents = []
    agents_dir = plugin_path / "agents"

    if not agents_dir.exists():
        return agents

    for agent_file in sorted(agents_dir.glob("*.md")):
        try:
            content = agent_file.read_text()
            frontmatter = parse_frontmatter(content)

            agent_name = agent_file.stem
            # Create relative path from repository root for GitHub link
            base_path = agent_file.parents[
                3
            ]  # Get repo root (three levels up from claude-plugins/plugin/agents)
            relative_path = agent_file.relative_to(base_path)

            agents.append(
                {
                    "name": frontmatter.get("name", agent_name),
                    "id": agent_name,
                    "description": frontmatter.get("description", ""),
                    "tools": frontmatter.get("tools", ""),
                    "model": frontmatter.get("model", ""),
                    "file_path": str(relative_path),
                }
            )
        except Exception as e:
            print(f"Error processing {agent_file}: {e}")

    return agents


def get_cursor_commands(cursor_path: Path) -> List[Dict[str, str]]:
    """Get all commands for cursor tools"""
    commands = []
    commands_dir = cursor_path / "commands"

    if not commands_dir.exists():
        return commands

    for cmd_file in sorted(commands_dir.glob("*.md")):
        try:
            # Resolve symlinks to get the actual file path
            resolved_file = cmd_file.resolve()
            content = resolved_file.read_text()
            frontmatter = parse_frontmatter(content)
            synopsis = extract_synopsis(content)

            command_name = cmd_file.stem
            # For cursor commands, use the full filename as the command name
            # e.g., 'git-commit-suggest' becomes '/git-commit-suggest'
            full_command_name = command_name

            # Extract display name for the command itself (last part after hyphen)
            parts = command_name.split("-", 1)
            if len(parts) > 1:
                display_name = parts[1]
            else:
                display_name = command_name

            # Fix synopsis for cursor commands to use proper format: /full-command-name
            if synopsis:
                # Replace the raw command with the full command name
                # E.g., "/sprint-summary <args>" becomes "/jira-sprint-summary <args>"
                cursor_synopsis = synopsis.replace(
                    f"/{display_name}", f"/{full_command_name}"
                )
                # Also handle cases where the synopsis might have the old :format
                cursor_synopsis = cursor_synopsis.replace(
                    f"/{command_name.split('-')[0]}:{display_name}",
                    f"/{full_command_name}",
                )
            else:
                cursor_synopsis = f"/{full_command_name}"

            # Create relative path from repository root for GitHub link
            # Handle both symlinked and regular files
            try:
                # Check if this is a symlink that points to somewhere within this repo
                if cmd_file.is_symlink():
                    resolved_file = cmd_file.resolve()
                    # Check if resolved file is within our repo
                    repo_base = cmd_file.parents[2]  # Should be the repo root
                    try:
                        # If the resolved file is within our repo, use its path
                        if resolved_file.is_relative_to(repo_base):
                            relative_path = resolved_file.relative_to(repo_base)
                        else:
                            # Symlink points outside our repo, use the symlink path itself
                            relative_path = cmd_file.relative_to(repo_base)
                    except (ValueError, AttributeError):
                        # Fallback for older Python versions or path issues
                        try:
                            resolved_str = str(resolved_file)
                            repo_str = str(repo_base)
                            if resolved_str.startswith(repo_str):
                                relative_path = resolved_file.relative_to(repo_base)
                            else:
                                relative_path = cmd_file.relative_to(repo_base)
                        except ValueError:
                            relative_path = Path("cursor") / "commands" / cmd_file.name
                else:
                    # Regular file, use normal path
                    base_path = cmd_file.parents[
                        2
                    ]  # Get repo root (two levels up from cursor/commands)
                    relative_path = cmd_file.relative_to(base_path)
            except (ValueError, OSError):
                # Final fallback: construct path assuming standard structure
                relative_path = Path("cursor") / "commands" / cmd_file.name

            commands.append(
                {
                    "name": display_name,
                    "full_command_name": full_command_name,
                    "description": frontmatter.get("description", ""),
                    "synopsis": cursor_synopsis,
                    "argument_hint": frontmatter.get("argument-hint", ""),
                    "file_path": str(relative_path),
                }
            )
        except Exception as e:
            print(f"Error processing {cmd_file}: {e}")

    return commands


def get_gemini_gems(gems_dir: Path, categories_data: Dict) -> List[Dict[str, any]]:
    """Get all Gemini Gems as individual tools for website display"""
    tools = []
    gems_file = gems_dir / "gems.yaml"

    if not gems_file.exists():
        return tools

    try:
        with open(gems_file, "r") as f:
            gems_data = yaml.safe_load(f)

        if not gems_data or "gems" not in gems_data:
            return tools

        for gem in gems_data["gems"]:
            gem_title = gem.get("title", "Untitled Gem")
            # Get category from categories.json based on gem title
            gem_category = get_gemini_gem_category(gem_title, categories_data)

            tools.append(
                {
                    "name": gem_title.lower().replace(" ", "-"),
                    "display_name": gem_title,
                    "description": gem.get("description", ""),
                    "category": gem_category,
                    "link": gem.get("link", ""),
                    "commands": [],
                    "skills": [],
                    "hooks": [],
                    "agents": [],
                    "has_readme": False,
                }
            )
    except Exception as e:
        print(f"Error processing {gems_file}: {e}")

    return tools


def load_categories(base_path: Path) -> Dict:
    """Load categories configuration"""
    categories_file = base_path / "categories.json"
    if categories_file.exists():
        with open(categories_file) as f:
            return json.load(f)
    return {
        "categories": {
            "general": {
                "name": "General",
                "description": "General-purpose tools and utilities",
                "claude_plugin_dirs": [],
                "cursor_commands": [],
            }
        }
    }


def update_categories_with_missing_items(
    categories_data: Dict, marketplace_data: Dict, base_path: Path
) -> bool:
    """Update categories.json to include any missing plugins, cursor commands, or gemini gems in 'general' category.
    Returns True if file was updated, False otherwise."""

    # Get all existing categorized items
    categorized_plugins = set()
    categorized_commands = set()
    categorized_gems = set()

    for category_data in categories_data["categories"].values():
        categorized_plugins.update(category_data.get("claude_plugin_dirs", []))
        categorized_commands.update(category_data.get("cursor_commands", []))
        categorized_gems.update(category_data.get("gemini_gems", []))

    # Get all actual plugins from marketplace
    actual_plugins = {plugin["name"] for plugin in marketplace_data["plugins"]}

    # Get all actual cursor commands
    actual_commands = set()
    cursor_path = base_path / "cursor" / "commands"
    if cursor_path.exists():
        for cmd_file in cursor_path.glob("*.md"):
            actual_commands.add(cmd_file.stem)

    # Get all actual gemini gems
    actual_gems = set()
    gems_file = base_path / "gemini-gems" / "gems.yaml"
    if gems_file.exists():
        try:
            with open(gems_file, "r") as f:
                gems_data = yaml.safe_load(f)
            if gems_data and "gems" in gems_data:
                for gem in gems_data["gems"]:
                    actual_gems.add(gem.get("title", "Untitled Gem"))
        except Exception as e:
            print(f"Error reading gems.yaml: {e}")

    # Find missing items
    missing_plugins = actual_plugins - categorized_plugins
    missing_commands = actual_commands - categorized_commands
    missing_gems = actual_gems - categorized_gems

    # If nothing missing, no update needed
    if not missing_plugins and not missing_commands and not missing_gems:
        return False

    # Ensure general category exists with proper structure
    if "general" not in categories_data["categories"]:
        categories_data["categories"]["general"] = {
            "name": "General",
            "description": "General-purpose tools and utilities",
            "claude_plugin_dirs": [],
            "cursor_commands": [],
            "gemini_gems": [],
        }

    general_category = categories_data["categories"]["general"]

    # Ensure the arrays exist
    if "claude_plugin_dirs" not in general_category:
        general_category["claude_plugin_dirs"] = []
    if "cursor_commands" not in general_category:
        general_category["cursor_commands"] = []
    if "gemini_gems" not in general_category:
        general_category["gemini_gems"] = []

    # Add missing plugins and commands to general category
    if missing_plugins:
        general_category["claude_plugin_dirs"].extend(sorted(missing_plugins))
        general_category["claude_plugin_dirs"] = sorted(
            list(set(general_category["claude_plugin_dirs"]))
        )
        print(
            f"Added {len(missing_plugins)} missing Claude plugins to general category: {', '.join(sorted(missing_plugins))}"
        )

    if missing_commands:
        general_category["cursor_commands"].extend(sorted(missing_commands))
        general_category["cursor_commands"] = sorted(
            list(set(general_category["cursor_commands"]))
        )
        print(
            f"Added {len(missing_commands)} missing Cursor commands to general category: {', '.join(sorted(missing_commands))}"
        )

    if missing_gems:
        general_category["gemini_gems"].extend(sorted(missing_gems))
        general_category["gemini_gems"] = sorted(
            list(set(general_category["gemini_gems"]))
        )
        print(
            f"Added {len(missing_gems)} missing Gemini Gems to general category: {', '.join(sorted(missing_gems))}"
        )

    return True


def get_plugin_category(plugin_name: str, categories_data: Dict) -> str:
    """Determine the category for a Claude plugin based on its directory name"""
    for category_key, category_data in categories_data["categories"].items():
        if plugin_name in category_data.get("claude_plugin_dirs", []):
            return category_key
    return "general"  # Default category


def get_cursor_category(command_name: str, categories_data: Dict) -> str:
    """Determine the category for a Cursor command based on configuration"""
    for category_key, category_data in categories_data["categories"].items():
        cursor_commands = category_data.get("cursor_commands", [])
        if command_name in cursor_commands:
            return category_key
    return "general"  # Default category


def get_gemini_gem_category(gem_title: str, categories_data: Dict) -> str:
    """Determine the category for a Gemini Gem based on configuration"""
    for category_key, category_data in categories_data["categories"].items():
        gemini_gems = category_data.get("gemini_gems", [])
        if gem_title in gemini_gems:
            return category_key
    return "general"  # Default category


def build_website_data():
    """Build complete website data structure"""
    # Get repository root (parent of scripts directory)
    base_path = Path(__file__).parent.parent
    marketplace_file = base_path / ".claude-plugin" / "marketplace.json"
    categories_file = base_path / "categories.json"

    with open(marketplace_file) as f:
        marketplace = json.load(f)

    # Load categories configuration
    categories_data = load_categories(base_path)

    # Update categories with any missing plugins/commands
    categories_updated = update_categories_with_missing_items(
        categories_data, marketplace, base_path
    )

    # Save updated categories back to file if needed
    if categories_updated:
        with open(categories_file, "w") as f:
            json.dump(categories_data, f, indent=2)
        print(f"Updated {categories_file} with missing items")

    website_data = {
        "name": marketplace["name"],
        "owner": marketplace["owner"]["name"],
        "categories": categories_data,
        "tools": {"claude_code": [], "cursor": [], "gemini": []},
    }

    # Process Claude Code plugins
    for plugin_info in marketplace["plugins"]:
        source = plugin_info["source"]

        # External plugins have object sources - skip local scanning
        if isinstance(source, dict):
            category = get_plugin_category(plugin_info["name"], categories_data)
            plugin_data = {
                "name": plugin_info["name"],
                "description": plugin_info["description"],
                "category": category,
                "commands": [],
                "skills": [],
                "hooks": [],
                "agents": [],
                "has_readme": False,
                "external": True,
                "source": source,
            }
            website_data["tools"]["claude_code"].append(plugin_data)
            continue

        # Local plugin - scan directory
        plugin_path = base_path / source

        # Get commands, skills, hooks, and agents
        commands = get_plugin_commands(plugin_path, plugin_info["name"])
        skills = get_plugin_skills(plugin_path)
        hooks = get_plugin_hooks(plugin_path)
        agents = get_plugin_agents(plugin_path)

        # Read README if exists
        readme_path = plugin_path / "README.md"

        # Determine category for this plugin
        category = get_plugin_category(plugin_info["name"], categories_data)

        plugin_data = {
            "name": plugin_info["name"],
            "description": plugin_info["description"],
            "category": category,
            "commands": commands,
            "skills": skills,
            "hooks": hooks,
            "agents": agents,
            "has_readme": readme_path.exists(),
        }

        website_data["tools"]["claude_code"].append(plugin_data)

    # Process Cursor commands (each command as individual tool)
    cursor_path = base_path / "cursor"
    if cursor_path.exists():
        cursor_commands = get_cursor_commands(cursor_path)

        # Each cursor command becomes an individual tool entry
        for cmd in cursor_commands:
            # Get the full command name from the file (e.g., git-commit-suggest, jira-sprint-summary)
            # Determine category for this cursor command
            category = get_cursor_category(cmd["full_command_name"], categories_data)

            cursor_tool_data = {
                "name": cmd[
                    "full_command_name"
                ],  # This will be added by get_cursor_commands
                "description": cmd["description"],
                "category": category,
                "commands": [cmd],  # Single command per tool
                "skills": [],
                "hooks": [],
                "agents": [],
                "has_readme": (cursor_path / "README.md").exists(),
            }

            website_data["tools"]["cursor"].append(cursor_tool_data)

    # Process Gemini Gems
    gemini_gems_path = base_path / "gemini-gems"
    if gemini_gems_path.exists():
        gems = get_gemini_gems(gemini_gems_path, categories_data)

        # Add each gem as an individual tool
        for gem_tool in gems:
            website_data["tools"]["gemini"].append(gem_tool)

    return website_data


if __name__ == "__main__":
    data = build_website_data()

    # Output as JSON (in docs directory at repo root)
    output_file = Path(__file__).parent.parent / "docs" / "data.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Website data written to {output_file}")

    # Calculate statistics
    claude_tools = data["tools"]["claude_code"]
    cursor_tools = data["tools"]["cursor"]
    gemini_tools = data["tools"]["gemini"]
    all_tools = claude_tools + cursor_tools + gemini_tools

    print(f"Total Claude Code plugins: {len(claude_tools)}")
    print(f"Total Cursor tools: {len(cursor_tools)}")
    print(f"Total Gemini Gems collections: {len(gemini_tools)}")
    print(f"Total tools: {len(all_tools)}")

    total_commands = sum(len(p["commands"]) for p in all_tools)
    print(f"Total commands: {total_commands}")

    total_skills = sum(len(p["skills"]) for p in all_tools)
    print(f"Total skills: {total_skills}")

    total_hooks = sum(len(p["hooks"]) for p in all_tools)
    print(f"Total hooks: {total_hooks}")

    total_agents = sum(len(p["agents"]) for p in all_tools)
    print(f"Total agents: {total_agents}")
