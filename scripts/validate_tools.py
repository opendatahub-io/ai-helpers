#!/usr/bin/env python3
"""
Validate categories.yaml structure and tool consistency

This script validates that:
1. categories.yaml file exists and contains valid YAML
2. All category entries are properly structured
3. All tools listed in categories exist in the filesystem
4. No duplicate tool names across categories
5. No duplicate tool names across different tool types (skills, commands, agents, gems)
6. Identifies tools that will be auto-categorized as 'General'

Usage:
    python3 scripts/validate_tools.py [categories.yaml]

Returns:
    0 on success
    1 on validation errors
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)


VALID_TOOL_TYPES = {"skill", "command", "agent", "gem"}


def title_to_slug(title: str) -> str:
    """Convert gem title to slug format (lowercase, spaces/special chars to hyphens)"""
    return re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")


def get_filesystem_tools_with_duplicates_check(
    helpers_dir: Path,
) -> Tuple[Dict[str, str], List[str]]:
    """Extract all tool names from the filesystem with their types and check for duplicates across types

    Returns:
        Tuple of (filesystem_tools dict, list of duplicate errors)
    """
    filesystem_tools = {}
    duplicate_errors = []
    # Track where each tool name is found: tool_name -> list of (type, location) tuples
    tool_locations = {}

    # Skills - directories in helpers/skills/
    skills_dir = helpers_dir / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        for item in skills_dir.iterdir():
            if item.is_dir():
                tool_name = item.name
                if tool_name not in tool_locations:
                    tool_locations[tool_name] = []
                tool_locations[tool_name].append(("skill", str(item)))
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
                if tool_name not in tool_locations:
                    tool_locations[tool_name] = []
                tool_locations[tool_name].append(("command", str(item)))
                if tool_name in filesystem_tools:
                    # Already exists with different type
                    continue
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
                if tool_name not in tool_locations:
                    tool_locations[tool_name] = []
                tool_locations[tool_name].append(("agent", str(item)))
                if tool_name in filesystem_tools:
                    # Already exists with different type
                    continue
                filesystem_tools[tool_name] = "agent"
            elif item.is_dir():
                # Directories in agents/ are incorrect - they should be .md files
                # But we still need to detect them as potential duplicates
                tool_name = item.name
                if tool_name not in tool_locations:
                    tool_locations[tool_name] = []
                tool_locations[tool_name].append(
                    ("agent (incorrect format)", str(item))
                )
                # Add an error for the incorrect format
                duplicate_errors.append(
                    f"Incorrect agent format: '{tool_name}' should be a .md file, not a directory ({item})"
                )
                if tool_name in filesystem_tools:
                    # Already exists with different type
                    continue
                filesystem_tools[tool_name] = "agent"

    # Gems - titles from gems.yaml
    gems_file = helpers_dir / "gems" / "gems.yaml"
    if gems_file.exists() and gems_file.is_file():
        if yaml is None:
            # Warn when gems.yaml exists but PyYAML is not available
            print(
                f"Warning: Found gems.yaml but PyYAML is not installed. "
                f"Gem validation skipped. Install PyYAML (pip install PyYAML) "
                f"or remove {gems_file} to disable gem validation.",
                file=sys.stderr,
            )
        else:
            try:
                with open(gems_file, "r", encoding="utf-8") as f:
                    gems_data = yaml.safe_load(f)

                if gems_data and "gems" in gems_data:
                    for gem in gems_data["gems"]:
                        if "title" in gem:
                            tool_name = title_to_slug(gem["title"])
                            if tool_name not in tool_locations:
                                tool_locations[tool_name] = []
                            tool_locations[tool_name].append(
                                ("gem", f"gems.yaml (title: {gem['title']})")
                            )
                            if tool_name in filesystem_tools:
                                # Already exists with different type
                                continue
                            filesystem_tools[tool_name] = "gem"
            except (yaml.YAMLError, IOError) as e:
                print(
                    f"Warning: Could not parse gems.yaml ({gems_file}): {e}",
                    file=sys.stderr,
                )

    # Check for duplicates across types
    for tool_name, locations in tool_locations.items():
        if len(locations) > 1:
            # Multiple locations found - this is a duplicate
            location_descriptions = []
            for tool_type, location in locations:
                location_descriptions.append(f"{tool_type} ({location})")
            duplicate_errors.append(
                f"Duplicate tool name '{tool_name}' found in multiple types: {', '.join(location_descriptions)}"
            )

    return filesystem_tools, duplicate_errors


def get_filesystem_tools(helpers_dir: Path) -> Dict[str, str]:
    """Extract all tool names from the filesystem with their types

    Returns:
        Dict mapping tool name to tool type
    """
    tools, _ = get_filesystem_tools_with_duplicates_check(helpers_dir)
    return tools


def load_categories_yaml(path: Path) -> Dict:
    """Load and parse categories.yaml file"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: {path} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {path}: {e}")
        sys.exit(1)


def validate_tool_structure(
    tool_name: str, index: int, category_name: str = None
) -> List[str]:
    """Validate individual tool structure"""
    errors = []
    tool_identifier = f"tool[{index}]"
    if category_name:
        tool_identifier += f" in category '{category_name}'"

    # Check tool name is a string and non-empty
    if not isinstance(tool_name, str):
        errors.append(
            f"{tool_identifier} must be a string, got {type(tool_name).__name__}"
        )
    elif not tool_name.strip():
        errors.append(f"{tool_identifier} is empty or whitespace only")

    return errors


def validate_category_tools(category_name: str, tools: List) -> List[str]:
    """Validate tools within a category"""
    errors = []

    if not isinstance(tools, list):
        errors.append(
            f"Category '{category_name}' must contain a list of tools, got {type(tools).__name__}"
        )
        return errors

    for i, tool_name in enumerate(tools):
        errors.extend(validate_tool_structure(tool_name, i, category_name))

    return errors


def validate_tool_names_unique(tools_data: Dict) -> List[str]:
    """Validate that tool names are unique across all categories"""
    errors = []
    seen_names = set()

    for category_name, tools in tools_data.items():
        if not isinstance(tools, list):
            continue

        for tool_name in tools:
            if not isinstance(tool_name, str):
                continue

            if tool_name in seen_names:
                errors.append(
                    f"Duplicate tool name: '{tool_name}' in category '{category_name}'"
                )
            else:
                seen_names.add(tool_name)

    return errors


def validate_tool_names_unique_across_types(helpers_dir: Path) -> List[str]:
    """Validate that tool names are unique across all tool types (skills, commands, agents, gems)"""
    _, duplicate_errors = get_filesystem_tools_with_duplicates_check(helpers_dir)
    return duplicate_errors


def validate_filesystem_tools_consistency(
    categories_data: Dict, helpers_dir: Path
) -> List[str]:
    """Validate filesystem tools consistency (info only - tools not in categories.yaml become General)"""
    errors = []

    # Get tools from filesystem
    filesystem_tools = get_filesystem_tools(helpers_dir)

    # Extract tool names from YAML structure (organized by category)
    yaml_tool_names = set()
    for category_name, tools in categories_data.items():
        if not isinstance(tools, list):
            continue
        for tool_name in tools:
            if isinstance(tool_name, str):
                yaml_tool_names.add(tool_name)

    # Check for tools that will become General (info only, not an error)
    uncategorized_tools = []
    for tool_name, expected_type in filesystem_tools.items():
        if tool_name not in yaml_tool_names:
            uncategorized_tools.append(f"{tool_name} (type: {expected_type})")

    if uncategorized_tools:
        print("Info: The following tools will be categorized as 'General':")
        for tool in uncategorized_tools:
            print(f"  - {tool}")

    return errors


def validate_categorized_tools_exist(
    categories_data: Dict, helpers_dir: Path
) -> List[str]:
    """Validate that tools listed in categories actually exist in the filesystem"""
    errors = []

    # Get tools from filesystem
    filesystem_tools = get_filesystem_tools(helpers_dir)

    # Check each tool in categories.yaml exists in filesystem
    for category_name, tools in categories_data.items():
        if not isinstance(tools, list):
            continue
        for tool_name in tools:
            if not isinstance(tool_name, str):
                continue
            if tool_name not in filesystem_tools:
                errors.append(
                    f"Tool '{tool_name}' in category '{category_name}' does not exist in filesystem"
                )

    return errors


def validate_categories_yaml(
    categories_data: Dict, helpers_dir: Path = None
) -> List[str]:
    """Run all validations on categories.yaml data"""
    errors = []

    # Check that the data is a dictionary
    if not isinstance(categories_data, dict):
        errors.append(
            "categories.yaml must contain a dictionary with categories as keys"
        )
        return errors

    # Validate tools within each category
    for category_name, tools in categories_data.items():
        errors.extend(validate_category_tools(category_name, tools))

    # Validate unique tool names across all categories
    errors.extend(validate_tool_names_unique(categories_data))

    # Validate unique tool names across all tool types (if helpers_dir is provided)
    if helpers_dir and helpers_dir.exists():
        errors.extend(validate_tool_names_unique_across_types(helpers_dir))

    # Validate that categorized tools exist in filesystem (if helpers_dir is provided)
    if helpers_dir and helpers_dir.exists():
        errors.extend(validate_categorized_tools_exist(categories_data, helpers_dir))

    # Validate filesystem tools consistency (if helpers_dir is provided)
    if helpers_dir and helpers_dir.exists():
        errors.extend(
            validate_filesystem_tools_consistency(categories_data, helpers_dir)
        )

    return errors


def main():
    """Main validation function"""
    # Determine categories.yaml path
    if len(sys.argv) > 1:
        categories_yaml_path = Path(sys.argv[1])
    else:
        # Default to categories.yaml in the current directory
        categories_yaml_path = Path("categories.yaml")

    # Determine helpers directory path
    helpers_dir = categories_yaml_path.parent / "helpers"

    # Load categories.yaml
    categories_data = load_categories_yaml(categories_yaml_path)

    # Validate categories.yaml
    errors = validate_categories_yaml(categories_data, helpers_dir)

    # Report results
    if errors:
        print("Tool validation errors found:")
        for error in errors:
            print(f"  ✗ {error}")
        print(f"\n{len(errors)} error(s) found.")
        sys.exit(1)
    else:
        print("✓ All tool validations passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
