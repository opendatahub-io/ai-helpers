#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pyyaml"]
# ///
"""
Build website data (docs/data.json) for ODH ai-helpers GitHub Pages.

Walks plugins/<plugin>/ (each plugin directory is a category), reading skill and
agent frontmatter, plus Gemini gems from gems/gems.yaml. The deprecated
odh-ai-helpers umbrella is skipped (it re-exports skills via symlinks).
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict

import yaml

UMBRELLA_PLUGIN = "odh-ai-helpers"

# Pretty display names for plugin categories; falls back to the plugin name.
CATEGORY_DISPLAY = {
    "odh-jira": "Jira",
    "odh-python-packaging": "Python Packaging",
    "odh-documentation": "Documentation",
    "odh-vllm": "vLLM",
    "odh-git": "Git",
    "odh-code-quality": "Code Quality",
    "odh-google-workspace": "Google Workspace",
    "odh-pytorch": "PyTorch",
    "odh-modules": "ODH Modules",
    "odh-konflux": "Konflux",
    "odh-rpm": "RPM",
    "odh-team": "Team",
    "odh-llm-d": "LLM-D",
    "odh-maas": "MaaS",
    "odh-security": "Security",
    "odh-general": "General",
}


def title_to_slug(title: str) -> str:
    """Convert a gem title to a slug (lowercase, non-alnum to hyphens)."""
    return re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")


def parse_frontmatter(path: Path) -> Dict:
    """Parse YAML frontmatter from a markdown file."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Warning: could not read {path}: {e}", file=sys.stderr)
        return {}
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(content[4:end]) or {}
    except yaml.YAMLError as e:
        print(f"Warning: bad frontmatter in {path}: {e}", file=sys.stderr)
        return {}


def build_website_data(base_path: Path) -> Dict:
    plugins_dir = base_path / "plugins"
    categories: Dict[str, Dict] = {}
    skills, agents, gems = [], [], []

    for plugin_dir in sorted(p for p in plugins_dir.iterdir() if p.is_dir()):
        if plugin_dir.name == UMBRELLA_PLUGIN:
            continue
        cat_key = plugin_dir.name
        categories[cat_key] = {"name": CATEGORY_DISPLAY.get(cat_key, cat_key)}

        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            for item in sorted(skills_dir.iterdir()):
                skill_md = item / "SKILL.md"
                if item.is_dir() and skill_md.is_file():
                    fm = parse_frontmatter(skill_md)
                    skills.append(
                        {
                            "name": item.name,
                            "id": item.name,
                            "description": fm.get("description", ""),
                            "category": cat_key,
                            "allowed_tools": fm.get("allowed-tools", ""),
                            "file_path": f"plugins/{plugin_dir.name}/skills/{item.name}/SKILL.md",
                        }
                    )

        agents_dir = plugin_dir / "agents"
        if agents_dir.is_dir():
            for item in sorted(agents_dir.iterdir()):
                if item.is_file() and item.suffix == ".md" and item.name.lower() != "readme.md":
                    fm = parse_frontmatter(item)
                    entry = {
                        "name": item.stem,
                        "id": item.stem,
                        "description": fm.get("description", ""),
                        "category": cat_key,
                        "tools": fm.get("tools", ""),
                        "file_path": f"plugins/{plugin_dir.name}/agents/{item.name}",
                    }
                    if fm.get("model"):
                        entry["model"] = fm["model"]
                    agents.append(entry)

    gems_file = base_path / "gems" / "gems.yaml"
    if gems_file.is_file():
        try:
            gems_data = yaml.safe_load(gems_file.read_text(encoding="utf-8")) or {}
            if gems_data.get("gems"):
                categories["gems"] = {"name": "Gemini Gems"}
                for gem in gems_data["gems"]:
                    title = gem.get("title", "")
                    if not title:
                        continue
                    gems.append(
                        {
                            "name": title_to_slug(title),
                            "description": gem.get("description", ""),
                            "category": "gems",
                            "link": gem.get("link", ""),
                        }
                    )
        except yaml.YAMLError as e:
            print(f"Warning: could not parse gems.yaml: {e}", file=sys.stderr)

    skills.sort(key=lambda x: x["name"])
    agents.sort(key=lambda x: x["name"])
    gems.sort(key=lambda x: x["name"])

    return {
        "name": "odh-ai-helpers",
        "owner": "ODH",
        "categories": categories,
        "tools": {"gemini": gems, "skills": skills, "agents": agents},
    }


if __name__ == "__main__":
    base = Path(__file__).parent.parent
    data = build_website_data(base)

    output_file = base / "docs" / "data.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Website data written to {output_file}")
    print(f"Total Skills: {len(data['tools']['skills'])}")
    print(f"Total Agents: {len(data['tools']['agents'])}")
    print(f"Total Gemini Gems: {len(data['tools']['gemini'])}")
