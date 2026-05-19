#!/usr/bin/env python3
"""
Fetch external plugin repositories and rewrite marketplace.json to use local paths.

Used during container builds so that external plugin skills are available
in non-interactive mode (claude -p), where Claude Code does not fetch URL sources.
"""

import json
import subprocess
import sys
from pathlib import Path


def main():
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent

    sources_path = repo_root / "claude-external-plugin-sources.json"
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"

    with open(sources_path, encoding="utf-8") as f:
        external_config = json.load(f)

    plugins = external_config.get("plugins", [])
    if not plugins:
        print("No external plugins to fetch.")
        return

    plugins_dir = repo_root / "external-plugins"
    plugins_dir.mkdir(exist_ok=True)

    fetched = {}
    for plugin in plugins:
        name = plugin["name"]
        url = plugin["source"]["url"]
        dest = plugins_dir / name

        if dest.exists():
            print(f"Skipping {name}: {dest} already exists")
        else:
            print(f"Cloning {name} from {url}...")
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(dest)],
                check=True,
            )

        fetched[name] = f"./external-plugins/{name}"

    with open(marketplace_path, encoding="utf-8") as f:
        marketplace = json.load(f)

    for entry in marketplace.get("plugins", []):
        if entry.get("name") in fetched:
            entry["source"] = fetched[entry["name"]]

    with open(marketplace_path, "w", encoding="utf-8") as f:
        json.dump(marketplace, f, indent=2)
        f.write("\n")

    print(f"Patched {marketplace_path} — replaced {len(fetched)} URL source(s) with local paths.")


if __name__ == "__main__":
    main()
