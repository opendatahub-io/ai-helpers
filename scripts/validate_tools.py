#!/usr/bin/env python3
"""
Validate the plugins/ directory structure and tool consistency.

Validates that:
1. Each plugins/<plugin>/ has a .claude-plugin/plugin.json whose "name" matches
   the directory name.
2. Every skill directory under plugins/<plugin>/skills/ contains a SKILL.md.
3. Agents under plugins/<plugin>/agents/ are .md files.
4. No skill/agent name is duplicated across plugins.

The deprecated backwards-compat umbrella (odh-ai-helpers) re-exports every skill
via symlinks, so it is excluded from duplicate detection.

Usage:
    python3 scripts/validate_tools.py [plugins_dir]

Returns 0 on success, 1 on validation errors.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# The deprecated umbrella re-exports every skill via symlinks; exclude it from
# duplicate detection and inventory scans.
UMBRELLA_PLUGIN = "odh-ai-helpers"


def get_plugin_tools(
    plugins_dir: Path, exclude: Tuple[str, ...] = (UMBRELLA_PLUGIN,)
) -> Tuple[List[Dict], List[str]]:
    """Scan plugins/<plugin>/{skills,agents} for tools.

    Returns (tools, duplicate_errors). Each tool is a dict with keys
    name, type, plugin, path.
    """
    tools: List[Dict] = []
    errors: List[str] = []
    locations: Dict[str, List[str]] = {}

    if not plugins_dir.is_dir():
        return tools, [f"plugins directory not found: {plugins_dir}"]

    for plugin_dir in sorted(p for p in plugins_dir.iterdir() if p.is_dir()):
        if plugin_dir.name in exclude:
            continue

        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                if item.is_dir():
                    tools.append(
                        {
                            "name": item.name,
                            "type": "skill",
                            "plugin": plugin_dir.name,
                            "path": str(item),
                        }
                    )
                    locations.setdefault(item.name, []).append(f"skill in {plugin_dir.name}")

        agents_dir = plugin_dir / "agents"
        if agents_dir.is_dir():
            for item in sorted(agents_dir.iterdir()):
                if item.is_file() and item.suffix == ".md" and item.name.lower() != "readme.md":
                    tools.append(
                        {
                            "name": item.stem,
                            "type": "agent",
                            "plugin": plugin_dir.name,
                            "path": str(item),
                        }
                    )
                    locations.setdefault(item.stem, []).append(f"agent in {plugin_dir.name}")

    for name, locs in locations.items():
        if len(locs) > 1:
            errors.append(f"Duplicate tool name '{name}' found in: {', '.join(locs)}")

    return tools, errors


def validate(plugins_dir: Path) -> List[str]:
    """Run all structural validations over the plugins/ directory."""
    errors: List[str] = []

    if not plugins_dir.is_dir():
        return [f"plugins directory not found: {plugins_dir}"]

    for plugin_dir in sorted(p for p in plugins_dir.iterdir() if p.is_dir()):
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            errors.append(f"{plugin_dir.name}: missing .claude-plugin/plugin.json")
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{plugin_dir.name}: invalid plugin.json: {e}")
            continue

        name = data.get("name")
        if not name:
            errors.append(f"{plugin_dir.name}: plugin.json missing 'name'")
        elif name != plugin_dir.name:
            errors.append(f"{plugin_dir.name}: plugin.json name '{name}' does not match directory")

        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                # is_dir()/is_file() follow symlinks, so the umbrella's
                # re-exported skills validate against their real targets.
                if item.is_dir() and not (item / "SKILL.md").is_file():
                    errors.append(f"{plugin_dir.name}/skills/{item.name}: missing SKILL.md")

    _, dup_errors = get_plugin_tools(plugins_dir)
    errors.extend(dup_errors)
    return errors


def main() -> None:
    if len(sys.argv) > 1:
        plugins_dir = Path(sys.argv[1])
    else:
        plugins_dir = Path(__file__).parent.parent / "plugins"

    errors = validate(plugins_dir)
    if errors:
        print("Tool validation errors found:")
        for error in errors:
            print(f"  ✗ {error}")
        print(f"\n{len(errors)} error(s) found.")
        sys.exit(1)

    print("✓ All tool validations passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
