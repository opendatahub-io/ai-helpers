#!/usr/bin/env python3
"""
PyPI license finder tool.

Simple tool to fetch license information from PyPI metadata.

Usage:
    ./scripts/find_license.py requests
    ./scripts/find_license.py django 4.2.0
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def fetch_pypi_data(package_name: str, version: str = None) -> dict:
    """Fetch package metadata from PyPI API."""
    if version:
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    else:
        url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"ERROR: Package '{package_name}' not found on PyPI")
            sys.exit(1)
        else:
            print(f"ERROR: Failed to fetch PyPI data: {e}")
            sys.exit(1)


def get_source_repository_url(data: dict) -> str:
    """Extract source repository URL from PyPI metadata."""
    info = data.get("info", {})

    # Check project URLs for source repository
    project_urls = info.get("project_urls", {})
    for key in ["Source", "Repository", "Source Code"]:
        if key in project_urls:
            return project_urls[key]

    # Check home page as fallback
    home_page = info.get("home_page", "")
    if home_page and any(
        host in home_page for host in ["github.com", "gitlab.com", "bitbucket.org"]
    ):
        return home_page

    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Find license information for Python packages"
    )
    parser.add_argument("package", help="Package name")
    parser.add_argument("version", nargs="?", help="Package version (optional)")

    args = parser.parse_args()

    # Fetch PyPI data
    print(
        f"Fetching PyPI data for {args.package}"
        + (f" {args.version}" if args.version else "")
    )
    data = fetch_pypi_data(args.package, args.version)

    # Check license fields - prioritize newer license_expression field
    info = data.get("info", {})

    # First check the newer SPDX license_expression field (PEP 639)
    license_expression = (info.get("license_expression") or "").strip()

    if license_expression and license_expression.lower() not in [
        "unknown",
        "none",
        "null",
        "",
    ]:
        print(f"LICENSE FOUND: {license_expression}")
        sys.exit(0)

    # Fall back to legacy license field for backwards compatibility
    license_info = (info.get("license") or "").strip()

    if license_info and license_info.lower() not in ["unknown", "none", "null", ""]:
        print(f"LICENSE FOUND: {license_info}")
        sys.exit(0)
    else:
        print(
            "No license found in PyPI metadata (checked both license_expression and license fields)"
        )

        # Provide source repository URL for fallback search
        repo_url = get_source_repository_url(data)
        if repo_url:
            print(f"SOURCE REPOSITORY: {repo_url}")
            print(
                "Use git:shallow-clone skill to search for LICENSE files in the repository"
            )
        else:
            print("No source repository URL found")
            print("LICENSE NOT FOUND")

        sys.exit(1)


if __name__ == "__main__":
    main()
