#!/usr/bin/env python3
"""Parse a product configuration YAML and emit structured JSON.

Usage:
    python3 parse-product-config.py configs/rhoai.yaml
    python3 parse-product-config.py configs/rhoai.yaml --section context_sources
    python3 parse-product-config.py configs/rhoai.yaml --section component_resolver
    python3 parse-product-config.py configs/rhoai.yaml --section version_mappings
    python3 parse-product-config.py configs/rhoai.yaml --section docs
    python3 parse-product-config.py configs/rhoai.yaml --section jira
    python3 parse-product-config.py configs/rhoai.yaml --resolve-component "Dashboard"
    python3 parse-product-config.py configs/rhoai.yaml --resolve-version "rhoai-2.18.GA1"
    python3 parse-product-config.py configs/rhoai.yaml --product-id
    python3 parse-product-config.py configs/rhoai.yaml --docs-repo
    python3 parse-product-config.py configs/rhoai.yaml --docs-branch
    python3 parse-product-config.py configs/rhoai.yaml --module-prefix concept
    python3 parse-product-config.py configs/rhoai.yaml --context-repos
    python3 parse-product-config.py configs/rhoai.yaml --always-include-repos
    python3 parse-product-config.py configs/rhoai.yaml --component-repo dashboard
    python3 parse-product-config.py configs/rhoai.yaml --jira-project-keys

Outputs JSON to stdout (for --section, --resolve-*) or plain text
(for convenience flags). Errors go to stderr.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml


_DOTENV_DENY_KEYS = frozenset({"PRODUCT_CONFIG_ROOT"})


def _load_dotenv() -> None:
    """Load .env file from project root (cwd) if it exists. Existing env vars take precedence."""
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key in _DOTENV_DENY_KEYS:
                continue
            if key not in os.environ:
                os.environ[key] = value


_load_dotenv()


def load_config(path: str) -> dict:
    """Load and return the YAML config as a dict."""
    config_path = Path(path)
    allowed_root = Path(os.environ.get("PRODUCT_CONFIG_ROOT", Path.cwd())).resolve()
    resolved = config_path.expanduser().resolve()
    if allowed_root != resolved and allowed_root not in resolved.parents:
        print(f"Error: config path escapes allowed root: {path}", file=sys.stderr)
        sys.exit(1)
    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        print(f"Error: config must be a YAML file: {path}", file=sys.stderr)
        sys.exit(1)
    if not resolved.is_file():
        print(f"Error: config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(resolved, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except OSError as exc:
        print(f"Error: cannot read config file: {exc}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(f"Error: invalid YAML in config file: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print(
            f"Error: config root must be a YAML mapping/object, got {type(data).__name__}",
            file=sys.stderr,
        )
        sys.exit(1)
    return data


def resolve_component(config: dict, name: str) -> dict | None:
    """Resolve a Jira component name to its canonical key and repo.

    Searches the component_resolver.components list for a match in jira_names.
    Returns the matching component dict or None.
    """
    resolver = config.get("component_resolver", {})
    components = resolver.get("components", [])
    name_lower = name.lower()
    for comp in components:
        jira_names = [n.lower() for n in comp.get("jira_names", [])]
        if name_lower in jira_names:
            return comp
    return None


def resolve_version(config: dict, version_string: str) -> dict:
    """Resolve a Jira version string to a branch name.

    Applies version_mappings rules in order. Returns a dict with:
    - matched: bool
    - pattern: the matching regex (if matched)
    - version: extracted version number (if matched)
    - branch: resolved branch name (if matched)
    """
    mappings = config.get("version_mappings", [])
    for mapping in mappings:
        pattern = mapping.get("jira_version_pattern", "")
        template = mapping.get("branch_template", "")
        try:
            match = re.match(pattern, version_string)
        except re.error as exc:
            print(
                f"Warning: invalid jira_version_pattern '{pattern}': {exc}",
                file=sys.stderr,
            )
            continue
        if match:
            # Extract version from first capture group
            version = match.group(1) if match.lastindex and match.lastindex >= 1 else version_string
            branch = template.replace("{version}", version)
            return {
                "matched": True,
                "pattern": pattern,
                "version": version,
                "branch": branch,
            }
    return {"matched": False, "version_string": version_string}


def get_context_sources(config: dict) -> list[dict]:
    """Return context sources with derived metadata."""
    sources = config.get("context_sources", [])
    result = []
    for source in sources:
        entry = dict(source)
        entry["always_include"] = source.get("always_include", False)
        result.append(entry)
    return result


def get_component_repo_map(config: dict) -> dict[str, str | None]:
    """Return a mapping of component key -> repo slug."""
    resolver = config.get("component_resolver", {})
    components = resolver.get("components", [])
    return {comp["key"]: comp.get("repo") for comp in components}


def get_jira_name_map(config: dict) -> dict[str, str]:
    """Return a mapping of Jira display name (lowered) -> component key."""
    resolver = config.get("component_resolver", {})
    components = resolver.get("components", [])
    result = {}
    for comp in components:
        for name in comp.get("jira_names", []):
            result[name.lower()] = comp["key"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse product configuration YAML")
    parser.add_argument("config", help="Path to product config YAML")
    parser.add_argument("--section", help="Extract a specific section")
    parser.add_argument("--resolve-component", metavar="NAME", help="Resolve a Jira component name")
    parser.add_argument(
        "--resolve-version", metavar="VERSION", help="Resolve a Jira version string"
    )

    # Convenience flags (replace product-config.sh pc_* functions)
    parser.add_argument("--product-id", action="store_true", help="Print product_id")
    parser.add_argument("--docs-repo", action="store_true", help="Print docs repo slug")
    parser.add_argument("--docs-branch", action="store_true", help="Print docs branch template")
    parser.add_argument(
        "--module-prefix",
        metavar="TYPE",
        help="Print module prefix for TYPE (concept, procedure, reference, assembly, snippet)",
    )
    parser.add_argument(
        "--context-repos",
        action="store_true",
        help="Print newline-separated list of context source repos",
    )
    parser.add_argument(
        "--always-include-repos",
        action="store_true",
        help="Print newline-separated list of always-include repos",
    )
    parser.add_argument(
        "--component-repo",
        metavar="KEY",
        help="Print repo for a component key",
    )
    parser.add_argument(
        "--jira-project-keys",
        action="store_true",
        help="Print newline-separated list of Jira project keys",
    )

    args = parser.parse_args()
    config = load_config(args.config)

    # --- Convenience flags (plain-text output) ---

    if args.product_id:
        value = config.get("product_id", "")
        if value:
            print(value)
        return

    if args.docs_repo:
        docs = config.get("docs", {})
        value = docs.get("repo", "")
        if value:
            print(value)
        return

    if args.docs_branch:
        docs = config.get("docs", {})
        value = docs.get("branch_template", "")
        if value:
            print(value)
        return

    if args.module_prefix is not None:
        docs = config.get("docs", {})
        prefixes = docs.get("module_prefixes", {})
        value = prefixes.get(args.module_prefix, "")
        if value:
            print(value)
        return

    if args.context_repos:
        for source in config.get("context_sources", []):
            repo = source.get("repo", "")
            if repo:
                print(repo)
        return

    if args.always_include_repos:
        for source in config.get("context_sources", []):
            if source.get("always_include", False):
                repo = source.get("repo", "")
                if repo:
                    print(repo)
        return

    if args.component_repo is not None:
        repo_map = get_component_repo_map(config)
        value = repo_map.get(args.component_repo)
        if value:
            print(value)
        return

    if args.jira_project_keys:
        jira = config.get("jira", {})
        for key in jira.get("project_keys", []):
            print(key)
        return

    # --- JSON output flags ---

    if args.resolve_component:
        result = resolve_component(config, args.resolve_component)
        if result is None:
            print(json.dumps({"found": False, "name": args.resolve_component}))
        else:
            result["found"] = True
            print(json.dumps(result))
        return

    if args.resolve_version:
        result = resolve_version(config, args.resolve_version)
        print(json.dumps(result))
        return

    if args.section:
        section_map = {
            "context_sources": lambda: get_context_sources(config),
            "component_resolver": lambda: config.get("component_resolver", {}),
            "version_mappings": lambda: config.get("version_mappings", []),
            "docs": lambda: config.get("docs", {}),
            "jira": lambda: config.get("jira", {}),
            "validators": lambda: config.get("validators", []),
            "component_repo_map": lambda: get_component_repo_map(config),
            "jira_name_map": lambda: get_jira_name_map(config),
        }
        if args.section not in section_map:
            print(
                f"Error: unknown section '{args.section}'. Available: {', '.join(section_map)}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(json.dumps(section_map[args.section](), indent=2))
        return

    # Default: output entire config as JSON
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
