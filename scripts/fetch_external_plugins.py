#!/usr/bin/env python3
"""
Fetch external plugin repositories and merge their content into the default plugin.

Claude Code only auto-loads the marketplace's default plugin (the one whose name
matches the marketplace name, i.e. ``odh-ai-helpers`` from ``./helpers``). Other
plugins listed in marketplace.json require explicit installation into the plugin
cache, which does not happen in non-interactive mode (``claude -p``).

This script works around that by cloning external plugin repos and copying their
skills, agents, and commands directly into the default plugin directory so they
are available without cache installation.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONTENT_DIRS = ("skills", "agents", "commands", "gems")


def main():
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent

    sources_path = repo_root / "claude-external-plugin-sources.json"
    default_plugin_dir = repo_root / "helpers"

    with open(sources_path, encoding="utf-8") as f:
        external_config = json.load(f)

    plugins = external_config.get("plugins", [])
    if not plugins:
        print("No external plugins to fetch.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        for plugin in plugins:
            name = plugin["name"]
            url = plugin["source"]["url"]
            clone_dest = tmp_dir / name

            print(f"Cloning {name} from {url}...")
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(clone_dest)],
                check=True,
            )

            copied = 0
            for content_dir in CONTENT_DIRS:
                src = clone_dest / content_dir
                if not src.is_dir():
                    continue
                dst = default_plugin_dir / content_dir
                dst.mkdir(exist_ok=True)
                for item in src.iterdir():
                    target = dst / item.name
                    if target.exists():
                        print(f"  WARNING: skipping {content_dir}/{item.name} (already exists)")
                        continue
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
                    copied += 1

            print(f"  Merged {copied} item(s) from {name} into {default_plugin_dir}")

    print("Done.")


if __name__ == "__main__":
    main()
