#!/usr/bin/env python3
"""
Build website data for ODH ai-helpers Github Pages
Loads tool information from centralized tools.yaml configuration
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict

import yaml


def load_categories_config(categories_path: Path) -> Dict:
    """Load categories configuration from categories.yaml."""

    if not categories_path.exists():
        print(f"Error: Categories configuration not found: {categories_path}")
        sys.exit(1)

    try:
        with open(categories_path, "r") as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        print(f"Error: Could not read categories configuration: {e}")
        sys.exit(1)


def title_to_slug(title: str) -> str:
    """Convert gem title to slug format (lowercase, spaces/special chars to hyphens)"""
    return re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")


def get_filesystem_tools(helpers_dir: Path) -> Dict[str, str]:
    """Extract all tool names from the filesystem with their types

    Returns:
        Dict mapping tool name to tool type
    """
    filesystem_tools = {}

    # Skills - directories in helpers/skills/
    skills_dir = helpers_dir / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        for item in skills_dir.iterdir():
            if item.is_dir():
                filesystem_tools[item.name] = "skill"

    # Commands - .md files in helpers/commands/
    commands_dir = helpers_dir / "commands"
    if commands_dir.exists() and commands_dir.is_dir():
        for item in commands_dir.iterdir():
            if item.is_file() and item.suffix == ".md":
                # Skip README.md files (case-insensitive)
                if item.name.lower() == "readme.md":
                    continue
                filesystem_tools[item.stem] = "command"

    # Agents - .md files in helpers/agents/
    agents_dir = helpers_dir / "agents"
    if agents_dir.exists() and agents_dir.is_dir():
        for item in agents_dir.iterdir():
            if item.is_file() and item.suffix == ".md":
                # Skip README.md files (case-insensitive)
                if item.name.lower() == "readme.md":
                    continue
                filesystem_tools[item.stem] = "agent"

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
                        filesystem_tools[tool_name] = "gem"
        except (yaml.YAMLError, IOError) as e:
            print(
                f"Warning: Could not parse gems.yaml ({gems_file}): {e}",
                file=sys.stderr,
            )

    return filesystem_tools


def get_tool_file_path(tool: Dict, base_path: Path) -> str:
    """Generate file path for a tool based on its type."""

    tool_type = tool["type"]
    tool_name = tool["name"]

    if tool_type == "skill":
        skill_file = base_path / "helpers" / "skills" / tool_name / "SKILL.md"
        if skill_file.exists():
            return f"helpers/skills/{tool_name}/SKILL.md"
        else:
            print(f"Warning: Skill file not found: {skill_file}")
            return f"helpers/skills/{tool_name}/SKILL.md"
    elif tool_type == "command":
        return f"helpers/commands/{tool_name}.md"
    elif tool_type == "agent":
        return f"helpers/agents/{tool_name}.md"
    elif tool_type == "gem":
        # Gems are external, no local file path
        return ""
    else:
        print(f"Warning: Unknown tool type '{tool_type}' for tool '{tool_name}'")
        return ""


def get_tool_metadata(tool: Dict, category: str, base_path: Path) -> Dict:
    """Get additional metadata for a tool by reading its file."""

    # Initialize metadata with basic info, description will be extracted from markdown
    metadata = {
        "name": tool["name"],
        "description": "",  # Will be populated from markdown frontmatter
        "category": category,
        "file_path": get_tool_file_path(tool, base_path),
    }

    tool_type = tool["type"]

    if tool_type == "skill":
        # Read additional skill metadata from SKILL.md
        skill_file = base_path / "helpers" / "skills" / tool["name"] / "SKILL.md"
        if skill_file.exists():
            try:
                content = skill_file.read_text()

                # Parse YAML frontmatter
                if content.startswith("---\n"):
                    end_marker = content.find("\n---\n", 4)
                    if end_marker != -1:
                        frontmatter_content = content[4:end_marker]
                        skill_data = yaml.safe_load(frontmatter_content)

                        metadata.update(
                            {
                                "description": skill_data.get("description", ""),
                                "id": tool["name"],
                                "allowed_tools": skill_data.get("allowed-tools", ""),
                            }
                        )
            except Exception as e:
                print(f"Warning: Could not read skill metadata from {skill_file}: {e}")

        # Add default fields for skills
        if "id" not in metadata:
            metadata["id"] = tool["name"]
        if "allowed_tools" not in metadata:
            metadata["allowed_tools"] = ""

    elif tool_type == "command":
        # Read command metadata from frontmatter
        cmd_file = base_path / "helpers" / "commands" / f"{tool['name']}.md"
        if cmd_file.exists():
            try:
                content = cmd_file.read_text()
                frontmatter = {}

                # Parse frontmatter - simple key: value parser
                if content.startswith("---\n"):
                    end_marker = content.find("\n---\n", 4)
                    if end_marker != -1:
                        frontmatter_content = content[4:end_marker]
                        for line in frontmatter_content.strip().split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                frontmatter[key.strip()] = value.strip()

                # Extract synopsis
                import re

                match = re.search(r"## Synopsis\s*```[^\n]*\n([^\n]+)", content, re.MULTILINE)

                # Only add synopsis to metadata if we found a non-empty match
                metadata_updates = {
                    "description": frontmatter.get("description", ""),
                    "argument_hint": frontmatter.get("argument-hint", ""),
                }
                if match:
                    synopsis = match.group(1).strip()
                    if synopsis:  # Only add if non-empty
                        metadata_updates["synopsis"] = synopsis

                metadata.update(metadata_updates)
            except Exception as e:
                print(f"Warning: Could not read command metadata from {cmd_file}: {e}")

        # Add default fields for commands
        if "synopsis" not in metadata:
            metadata["synopsis"] = f"/{tool['name']}"
        if "argument_hint" not in metadata:
            metadata["argument_hint"] = ""

    elif tool_type == "agent":
        # Read agent metadata from frontmatter
        agent_file = base_path / "helpers" / "agents" / f"{tool['name']}.md"
        if agent_file.exists():
            try:
                content = agent_file.read_text()

                # Parse YAML frontmatter
                if content.startswith("---\n"):
                    end_marker = content.find("\n---\n", 4)
                    if end_marker != -1:
                        frontmatter_content = content[4:end_marker]
                        agent_data = yaml.safe_load(frontmatter_content)

                        metadata_updates = {
                            "description": agent_data.get("description", ""),
                            "id": tool["name"],
                            "tools": agent_data.get("tools", ""),
                        }

                        # Only include model if it's not empty
                        model = agent_data.get("model", "")
                        if model:
                            metadata_updates["model"] = model

                        metadata.update(metadata_updates)
            except Exception as e:
                print(f"Warning: Could not read agent metadata from {agent_file}: {e}")

        # Add default fields for agents
        if "id" not in metadata:
            metadata["id"] = tool["name"]
        if "tools" not in metadata:
            metadata["tools"] = ""

    elif tool_type == "gem":
        # For gems, get description and link from gems.yaml by matching tool name
        link = ""
        description = ""

        gemini_gems_path = base_path / "helpers" / "gems" / "gems.yaml"
        if gemini_gems_path.exists():
            try:
                with open(gemini_gems_path) as f:
                    gems_data = yaml.safe_load(f)

                # Find matching gem by converting gem title to kebab-case
                def title_to_kebab_case(title):
                    """Convert gem title to kebab-case for matching with tool names"""
                    import re

                    # Replace spaces and special characters with hyphens
                    kebab = re.sub(r"[^\w\s-]", "", title.lower())
                    kebab = re.sub(r"[-\s]+", "-", kebab)
                    return kebab.strip("-")

                tool_name = tool["name"]

                for gem in gems_data.get("gems", []):
                    gem_title = gem.get("title", "")
                    if gem_title and title_to_kebab_case(gem_title) == tool_name:
                        link = gem.get("link", "")
                        # Use description from gems.yaml if available
                        if "description" in gem:
                            description = gem.get("description", "")
                        break
            except Exception as e:
                print(f"Warning: Could not read gemini gems data: {e}")

        metadata.update(
            {
                "description": description,
                "link": link,
            }
        )

    return metadata


def build_website_data():
    """Build complete website data structure"""
    # Get repository root (parent of scripts directory)
    base_path = Path(__file__).parent.parent
    categories_path = base_path / "categories.yaml"

    # Load categories configuration
    categories_config = load_categories_config(categories_path) if categories_path.exists() else {}

    # Get filesystem tools to infer types
    helpers_dir = base_path / "helpers"
    filesystem_tools = get_filesystem_tools(helpers_dir)

    # Collect tools that are already in categories to identify General tools
    categorized_tools = set()
    for category_name, tools in categories_config.items():
        if isinstance(tools, list):
            categorized_tools.update(tools)

    # Check for duplicate tool names
    all_tools_in_categories = []
    for category_name, tools in categories_config.items():
        if isinstance(tools, list):
            all_tools_in_categories.extend(tools)

    # Validate no duplicates
    seen_tools = set()
    duplicate_tools = set()
    for tool_name in all_tools_in_categories:
        if tool_name in seen_tools:
            duplicate_tools.add(tool_name)
        seen_tools.add(tool_name)

    if duplicate_tools:
        print("Error: Duplicate tool names found in categories:")
        for tool in duplicate_tools:
            print(f"  - {tool}")
        sys.exit(1)

    # Identify tools that should be in General category (not in any category)
    general_tools = []
    for tool_name in filesystem_tools.keys():
        if tool_name not in categorized_tools:
            general_tools.append(tool_name)

    # Create complete categories structure (including General if there are uncategorized tools)
    categories = {}
    if general_tools:
        categories["general"] = {"name": "General"}
    for category_key in categories_config.keys():
        # Convert category names to lowercase keys for consistent filtering
        categories[category_key.lower()] = {"name": category_key}

    website_data = {
        "name": "odh-ai-helpers",
        "owner": "ODH",
        "categories": categories,
        "tools": {"gemini": [], "skills": [], "commands": [], "agents": []},
    }

    # Process General tools first (uncategorized tools)
    if general_tools:
        for tool_name in general_tools:
            if tool_name in filesystem_tools:
                tool_type = filesystem_tools[tool_name]
                tool_metadata = get_tool_metadata(
                    {"name": tool_name, "type": tool_type}, "general", base_path
                )

                if tool_type == "skill":
                    website_data["tools"]["skills"].append(tool_metadata)
                elif tool_type == "command":
                    website_data["tools"]["commands"].append(tool_metadata)
                elif tool_type == "agent":
                    website_data["tools"]["agents"].append(tool_metadata)
                elif tool_type == "gem":
                    website_data["tools"]["gemini"].append(tool_metadata)

    # Process tools by category
    for category_name, tools in categories_config.items():
        if not isinstance(tools, list):
            print(f"Warning: Category '{category_name}' does not contain a list of tools")
            continue

        for tool_name in tools:
            # Validate tool name is a string
            if not isinstance(tool_name, str):
                print(
                    "Warning: Tool name must be a string in "
                    f"category '{category_name}': {tool_name}"
                )
                continue

            # Get tool type from filesystem
            if tool_name not in filesystem_tools:
                print(f"Warning: Tool '{tool_name}' not found in filesystem, skipping")
                continue

            tool_type = filesystem_tools[tool_name]
            tool_metadata = get_tool_metadata(
                {"name": tool_name, "type": tool_type}, category_name.lower(), base_path
            )

            if tool_type == "skill":
                website_data["tools"]["skills"].append(tool_metadata)
            elif tool_type == "command":
                website_data["tools"]["commands"].append(tool_metadata)
            elif tool_type == "agent":
                website_data["tools"]["agents"].append(tool_metadata)
            elif tool_type == "gem":
                website_data["tools"]["gemini"].append(tool_metadata)

    # Sort all tool arrays alphabetically by name to ensure consistent ordering
    website_data["tools"]["skills"].sort(key=lambda x: x["name"])
    website_data["tools"]["commands"].sort(key=lambda x: x["name"])
    website_data["tools"]["agents"].sort(key=lambda x: x["name"])
    website_data["tools"]["gemini"].sort(key=lambda x: x["name"])

    return website_data


if __name__ == "__main__":
    data = build_website_data()

    # Output as JSON (in docs directory at repo root)
    output_file = Path(__file__).parent.parent / "docs" / "data.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Website data written to {output_file}")

    # Calculate statistics for new tool structure
    skills_tools = data["tools"]["skills"]
    commands_tools = data["tools"]["commands"]
    agents_tools = data["tools"]["agents"]
    gemini_tools = data["tools"]["gemini"]
    all_tools = skills_tools + commands_tools + agents_tools + gemini_tools

    print(f"Total Skills: {len(skills_tools)}")
    print(f"Total Commands: {len(commands_tools)}")
    print(f"Total Agents: {len(agents_tools)}")
    print(f"Total Gemini Gems: {len(gemini_tools)}")
    print(f"Total tools: {len(all_tools)}")
