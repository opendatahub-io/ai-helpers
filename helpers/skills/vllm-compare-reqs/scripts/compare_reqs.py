#!/usr/bin/env python3
"""
Compare vllm requirements files between versions.

This script fetches requirements files from the vllm GitHub repository
and provides intelligent comparison with support for hardware variants.
"""

import argparse
import sys
from typing import Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE_URL = "https://raw.githubusercontent.com/vllm-project/vllm"

# Variant definitions: which requirements files and Dockerfiles to compare
VARIANT_CONFIG = {
    "rocm": {
        "requirements": ["common.txt", "rocm.txt", "rocm-build.txt"],
        "dockerfiles": ["docker/Dockerfile.rocm", "docker/Dockerfile.rocm_base"],
    },
    "cuda": {
        "requirements": ["common.txt", "cuda.txt"],  # No cuda-build.txt
        "dockerfiles": ["docker/Dockerfile"],
    },
    "cpu": {
        "requirements": ["common.txt", "cpu.txt", "cpu-build.txt"],
        "dockerfiles": ["docker/Dockerfile.cpu"],
    },
    "tpu": {
        "requirements": ["common.txt", "tpu.txt"],  # No tpu-build.txt
        "dockerfiles": ["docker/Dockerfile.tpu"],
    },
    "xpu": {
        "requirements": ["common.txt", "xpu.txt"],  # No xpu-build.txt
        "dockerfiles": ["docker/Dockerfile.xpu"],
    },
}

VARIANTS = list(VARIANT_CONFIG.keys())


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def fetch_file(version: str, filename: str) -> List[str]:
    """Fetch a requirements file or Dockerfile from GitHub."""
    # Determine the path based on whether it's a Dockerfile or requirements file
    if filename.startswith("docker/"):
        url = f"{BASE_URL}/{version}/{filename}"
    else:
        url = f"{BASE_URL}/{version}/requirements/{filename}"

    try:
        with urlopen(url, timeout=10) as response:
            content = response.read().decode("utf-8")
            return content.splitlines()
    except (HTTPError, URLError):
        return None


def parse_dockerfile_args(lines: List[str]) -> Dict[str, str]:
    """
    Parse ARG statements from a Dockerfile.
    Returns dict of {ARG_NAME: value}
    """
    args = {}
    for line in lines:
        line = line.strip()
        if line.startswith("ARG "):
            # Parse ARG statements like: ARG TRITON_BRANCH="57c693b6"
            arg_content = line[4:].strip()  # Remove "ARG "
            if "=" in arg_content:
                key, value = arg_content.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')
                args[key] = value
    return args


def compare_dockerfiles(old_lines: List[str], new_lines: List[str]) -> Dict[str, List[str]]:
    """
    Compare Dockerfile ARG statements between versions.
    Returns dict with keys: 'changed', 'added', 'removed'
    """
    old_args = parse_dockerfile_args(old_lines)
    new_args = parse_dockerfile_args(new_lines)

    changed = []
    added = []
    removed = []

    # Find changed ARGs
    for arg_name in old_args:
        if arg_name in new_args:
            if old_args[arg_name] != new_args[arg_name]:
                changed.append(f"{arg_name}={old_args[arg_name]} → {arg_name}={new_args[arg_name]}")
        else:
            removed.append(f"{arg_name}={old_args[arg_name]}")

    # Find added ARGs
    for arg_name in new_args:
        if arg_name not in old_args:
            added.append(f"{arg_name}={new_args[arg_name]}")

    return {"changed": changed, "added": added, "removed": removed, "special": []}


def parse_requirement_line(line: str) -> Tuple[str, str]:
    """
    Parse a requirement line into (package_name, full_line).

    Extracts the package name from lines like:
    - package==1.0.0
    - package>=1.0.0
    - --extra-index-url https://...
    - # comments
    """
    line = line.strip()

    # Skip empty lines and comments
    if not line or line.startswith("#"):
        return None, line

    # Handle special lines (--extra-index-url, -r, etc.)
    if line.startswith("-"):
        return None, line

    # Extract package name (before ==, >=, <, >, etc.)
    for sep in ["==", ">=", "<=", ">", "<", "!=", "~=", ";"]:
        if sep in line:
            return line.split(sep)[0].strip(), line

    # No version specifier
    return line.strip(), line


def compare_files(
    old_lines: List[str], new_lines: List[str], pretty: bool = True
) -> Dict[str, List[str]]:
    """
    Compare two requirements files and categorize changes.

    Returns:
        Dict with keys: 'changed', 'added', 'removed', 'special'
    """
    # Parse both files
    old_packages = {}
    new_packages = {}
    old_special = []
    new_special = []

    for line in old_lines:
        pkg_name, full_line = parse_requirement_line(line)
        if pkg_name is None:
            if full_line and not full_line.startswith("#"):
                old_special.append(full_line)
        else:
            old_packages[pkg_name] = full_line

    for line in new_lines:
        pkg_name, full_line = parse_requirement_line(line)
        if pkg_name is None:
            if full_line and not full_line.startswith("#"):
                new_special.append(full_line)
        else:
            new_packages[pkg_name] = full_line

    # Find changes
    changed = []
    added = []
    removed = []
    special_changes = []

    # Check for changed packages
    for pkg_name in old_packages:
        if pkg_name in new_packages:
            if old_packages[pkg_name] != new_packages[pkg_name]:
                changed.append(f"{old_packages[pkg_name]} → {new_packages[pkg_name]}")
        else:
            removed.append(old_packages[pkg_name])

    # Check for added packages
    for pkg_name in new_packages:
        if pkg_name not in old_packages:
            added.append(new_packages[pkg_name])

    # Check for special line changes
    for line in old_special:
        if line not in new_special:
            special_changes.append(f"- {line}")
    for line in new_special:
        if line not in old_special:
            special_changes.append(f"+ {line}")

    return {
        "changed": changed,
        "added": added,
        "removed": removed,
        "special": special_changes,
    }


def print_changes(filename: str, changes: Dict[str, List[str]], pretty: bool = True):
    """Print changes in a formatted way."""
    # Determine if this is a Dockerfile for better labeling
    is_dockerfile = filename.startswith("docker/")
    emoji = "🐳" if is_dockerfile else "📄"

    if pretty:
        # Pretty mode with emojis
        print(f"\n{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
        print(f"{Colors.BOLD}{emoji} {filename}{Colors.RESET}")
        print(f"{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")

        has_changes = False

        if changes["changed"]:
            has_changes = True
            print(f"{Colors.YELLOW}📦 Changed:{Colors.RESET}")
            for line in changes["changed"]:
                print(f"  {line}")
            print()

        if changes["added"]:
            has_changes = True
            print(f"{Colors.GREEN}➕ Added:{Colors.RESET}")
            for line in changes["added"]:
                print(f"  {line}")
            print()

        if changes["removed"]:
            has_changes = True
            print(f"{Colors.RED}➖ Removed:{Colors.RESET}")
            for line in changes["removed"]:
                print(f"  {line}")
            print()

        if changes["special"]:
            has_changes = True
            print(f"{Colors.BLUE}🔧 Infrastructure/Special:{Colors.RESET}")
            for line in changes["special"]:
                print(f"  {line}")
            print()

        if not has_changes:
            print("No changes detected between versions.\n")
    else:
        # Regular unified diff mode
        print(f"\n=== {filename} ===\n")
        # Simple line-by-line comparison
        all_changes = (
            [f"- {line}" for line in changes["removed"]]
            + [f"+ {line}" for line in changes["added"]]
            + [f"~ {line}" for line in changes["changed"]]
        )
        if all_changes:
            for line in all_changes:
                print(line)
        else:
            print("No changes detected")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Compare vllm requirements files between versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s v0.13.0 v0.14.0 rocm                    # Compare rocm (runtime + build + Dockerfiles)
  %(prog)s v0.13.0 v0.14.0 rocm --pretty           # Pretty output (default)
  %(prog)s v0.13.0 v0.14.0 rocm-build.txt          # Compare specific file
  %(prog)s v0.13.0 v0.14.0 docker/Dockerfile.rocm  # Compare specific Dockerfile
        """,
    )

    parser.add_argument("version1", help="First version (e.g., v0.13.0)")
    parser.add_argument("version2", help="Second version (e.g., v0.14.0)")
    parser.add_argument(
        "variant_or_file",
        help="Variant (rocm, cuda, cpu, tpu, xpu) or specific file (e.g., rocm-build.txt)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Show clean categorized output (default)",
    )
    parser.add_argument("--no-pretty", action="store_true", help="Show simple diff output")

    args = parser.parse_args()

    # Determine pretty mode
    pretty = not args.no_pretty

    # Determine which files to compare
    variant_or_file = args.variant_or_file.lower()

    if variant_or_file in VARIANTS:
        # Variant mode - use predefined configuration
        config = VARIANT_CONFIG[variant_or_file]
        files_to_compare = config["requirements"].copy()

        # Add Dockerfiles if defined
        if "dockerfiles" in config and config["dockerfiles"]:
            files_to_compare.extend(config["dockerfiles"])
            dockerfile_note = " + Dockerfiles"
        else:
            dockerfile_note = ""

        header = (
            f"=== Comparing {variant_or_file} variant"
            f" (runtime + build{dockerfile_note}):"
            f" {args.version1} -> {args.version2} ==="
        )
        print(f"\n{Colors.BOLD}{header}{Colors.RESET}\n")
    else:
        # Specific file mode
        files_to_compare = [variant_or_file]
        header = f"=== Comparing {variant_or_file}: {args.version1} -> {args.version2} ==="
        print(f"\n{Colors.BOLD}{header}{Colors.RESET}\n")

    # Fetch and compare files
    any_success = False
    urls_compared = []
    all_changes = {}  # Store changes for summary table

    for filename in files_to_compare:
        print(f"Fetching {filename} for {args.version1}...")
        old_lines = fetch_file(args.version1, filename)

        if old_lines is None:
            print(
                f"{Colors.RED}Warning: Could not fetch {filename} for {args.version1}{Colors.RESET}"
            )
            continue

        print(f"Fetching {filename} for {args.version2}...")
        new_lines = fetch_file(args.version2, filename)

        if new_lines is None:
            print(
                f"{Colors.RED}Warning: Could not fetch {filename} for {args.version2}{Colors.RESET}"
            )
            continue

        any_success = True
        urls_compared.append((filename, args.version1, args.version2))

        # Compare and store changes (use different function for Dockerfiles)
        if filename.startswith("docker/"):
            changes = compare_dockerfiles(old_lines, new_lines)
        else:
            changes = compare_files(old_lines, new_lines, pretty)
        all_changes[filename] = changes

    if not any_success:
        print(f"\n{Colors.RED}Error: Could not fetch any requirements files{Colors.RESET}")
        return 1

    # Print summary table if pretty mode
    if pretty and len(all_changes) > 0:
        print(f"\n{Colors.BOLD}📊 Change Summary Table:{Colors.RESET}\n")

        # Collect all package changes across files
        table_rows = []
        for filename, changes in all_changes.items():
            is_dockerfile = filename.startswith("docker/")

            # Process changed packages
            for change_line in changes["changed"]:
                if " → " in change_line:
                    old_part, new_part = change_line.split(" → ", 1)

                    if is_dockerfile:
                        # Dockerfile ARG format: ARG_NAME=value
                        if "=" in old_part and "=" in new_part:
                            old_pkg = old_part.split("=")[0].strip()
                            new_pkg = new_part.split("=")[0].strip()
                            old_ver = old_part.split("=", 1)[1].strip()
                            new_ver = new_part.split("=", 1)[1].strip()
                        else:
                            # Fallback for unexpected format
                            old_pkg = old_part.strip()
                            new_pkg = new_part.strip()
                            old_ver = ""
                            new_ver = ""
                    else:
                        # Requirements file format: package==version or package>=version
                        old_pkg = (
                            old_part.split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split(">")[0]
                            .split("<")[0]
                            .strip()
                        )
                        new_pkg = (
                            new_part.split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split(">")[0]
                            .split("<")[0]
                            .strip()
                        )

                        # Extract versions (everything after package name)
                        old_ver = old_part.replace(old_pkg, "").strip()
                        new_ver = new_part.replace(new_pkg, "").strip()

                    table_rows.append((filename, old_pkg, old_ver, new_ver, "Changed"))

            # Process added packages
            for add_line in changes["added"]:
                if is_dockerfile:
                    # Dockerfile ARG format: ARG_NAME=value
                    if "=" in add_line:
                        pkg_name = add_line.split("=")[0].strip()
                        version = add_line.split("=", 1)[1].strip()
                    else:
                        pkg_name = add_line.strip()
                        version = ""
                else:
                    # Requirements file format
                    pkg_name = (
                        add_line.split("==")[0]
                        .split(">=")[0]
                        .split("<=")[0]
                        .split(">")[0]
                        .split("<")[0]
                        .split(";")[0]
                        .split("#")[0]
                        .strip()
                    )
                    version = add_line.replace(pkg_name, "").split("#")[0].strip()
                table_rows.append((filename, pkg_name, "-", version, "Added"))

            # Process removed packages
            for rem_line in changes["removed"]:
                if is_dockerfile:
                    # Dockerfile ARG format: ARG_NAME=value
                    if "=" in rem_line:
                        pkg_name = rem_line.split("=")[0].strip()
                        version = rem_line.split("=", 1)[1].strip()
                    else:
                        pkg_name = rem_line.strip()
                        version = ""
                else:
                    # Requirements file format
                    pkg_name = (
                        rem_line.split("==")[0]
                        .split(">=")[0]
                        .split("<=")[0]
                        .split(">")[0]
                        .split("<")[0]
                        .split(";")[0]
                        .split("#")[0]
                        .strip()
                    )
                    version = rem_line.replace(pkg_name, "").split("#")[0].strip()
                table_rows.append((filename, pkg_name, version, "-", "Removed"))

        if table_rows:
            # Print table header
            print(
                f"{'File':<20} {'Package':<35} {'Old Version':<25} {'New Version':<25} {'Type':<10}"
            )
            print("─" * 120)

            # Print rows with color coding
            for filename, pkg, old_ver, new_ver, change_type in table_rows:
                # Truncate long values
                display_file = filename if len(filename) <= 19 else filename[:16] + "..."
                display_pkg = pkg if len(pkg) <= 34 else pkg[:31] + "..."
                display_old = old_ver if len(old_ver) <= 24 else old_ver[:21] + "..."
                display_new = new_ver if len(new_ver) <= 24 else new_ver[:21] + "..."

                # Color code the type
                if change_type == "Changed":
                    type_colored = f"{Colors.YELLOW}{change_type}{Colors.RESET}"
                elif change_type == "Added":
                    type_colored = f"{Colors.GREEN}{change_type}{Colors.RESET}"
                else:  # Removed
                    type_colored = f"{Colors.RED}{change_type}{Colors.RESET}"

                row = (
                    f"{display_file:<20} {display_pkg:<35}"
                    f" {display_old:<25} {display_new:<25}"
                    f" {type_colored}"
                )
                print(row)
            print()

    # Display detailed changes
    for filename, changes in all_changes.items():
        print_changes(filename, changes, pretty)

    # Display URLs
    print(f"\n{Colors.BOLD}URLs compared:{Colors.RESET}")
    for filename, v1, v2 in urls_compared:
        print(f"  {filename}:")
        if filename.startswith("docker/"):
            print(f"    {BASE_URL}/{v1}/{filename}")
            print(f"    {BASE_URL}/{v2}/{filename}")
        else:
            print(f"    {BASE_URL}/{v1}/requirements/{filename}")
            print(f"    {BASE_URL}/{v2}/requirements/{filename}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
