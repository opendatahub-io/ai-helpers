#!/usr/bin/env python3
"""
PyPI package inspection tool.

This tool provides comprehensive analysis of Python packages on PyPI to help
determine build requirements, customization needs, and compatibility for the
wheels builder project.

Usage:
    ./bin/pypi_inspect.py torch
    ./bin/pypi_inspect.py torch 2.7.1
"""

import argparse
import json
import logging
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)


class PackageNotFoundError(Exception):
    """Raised when a package is not found on PyPI."""

    pass


class PyPIInspector:
    """Main class for inspecting PyPI packages."""

    def __init__(self, pypi_base_url: str = "https://pypi.org/pypi"):
        """Initialize the inspector with a PyPI base URL."""
        self.pypi_base_url = pypi_base_url.rstrip("/")

    def get_package_metadata(
        self, package_name: str, version: str | None = None
    ) -> dict[str, Any]:
        """
        Fetch package metadata from PyPI JSON API.

        Args:
            package_name: Name of the package
            version: Optional specific version to query

        Returns:
            Dictionary containing package metadata

        Raises:
            PackageNotFoundError: If package or version not found
        """
        if version:
            url = f"{self.pypi_base_url}/{package_name}/{version}/json"
        else:
            url = f"{self.pypi_base_url}/{package_name}/json"

        logger.debug(f"Fetching metadata from: {url}")

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                if version:
                    raise PackageNotFoundError(
                        f"Package '{package_name}' version '{version}' not found on PyPI"
                    ) from e
                else:
                    raise PackageNotFoundError(
                        f"Package '{package_name}' not found on PyPI"
                    ) from e
            else:
                raise RuntimeError(f"HTTP error {e.code}: {e.reason}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to fetch package metadata: {e}") from e

    def normalize_url_label(self, label: str) -> str:
        """Normalize project URL labels."""
        label_mapping = {
            "homepage": "Homepage",
            "repository": "Repository",
            "documentation": "Documentation",
            "bug tracker": "Bug Tracker",
            "bug reports": "Bug Tracker",
            "issues": "Bug Tracker",
            "source": "Source",
            "source code": "Source",
            "download": "Download",
            "changelog": "Changelog",
            "funding": "Funding",
            "sponsor": "Funding",
        }
        return label_mapping.get(label.lower(), label.title())

    def extract_license_classifiers(self, classifiers: list[str]) -> list[str]:
        """Extract license information from classifiers."""
        license_classifiers = []
        for classifier in classifiers:
            if classifier.startswith("License ::"):
                # Extract the license part after "License :: "
                license_part = classifier.split("License :: ", 1)[1]
                license_classifiers.append(license_part)
        return license_classifiers

    def truncate_text(self, text: str, max_length: int = 75) -> str:
        """Truncate text to specified length."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def analyze_current_version_distributions(
        self, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze available distributions for the current version being inspected.

        Returns:
            Dictionary with distribution analysis for the current version
        """
        # Get current version info
        info = metadata.get("info", {})
        current_version = info.get("version")
        releases = metadata.get("releases", {})

        analysis = {
            "has_sdist": False,
            "has_wheels": False,
            "wheel_types": set(),
        }

        # Get files for the current version
        if current_version and current_version in releases:
            files = releases[current_version]

            for file_info in files:
                filename = file_info.get("filename", "")
                packagetype = file_info.get("packagetype", "")

                if packagetype == "sdist" or filename.endswith((".tar.gz", ".zip")):
                    analysis["has_sdist"] = True
                elif packagetype == "bdist_wheel" or filename.endswith(".whl"):
                    analysis["has_wheels"] = True

                    # Extract wheel type information
                    if filename.endswith(".whl"):
                        wheel_parts = filename.split("-")
                        if len(wheel_parts) >= 5:
                            platform_tag = wheel_parts[-1].replace(".whl", "")
                            abi_tag = wheel_parts[-2]
                            analysis["wheel_types"].add(f"{abi_tag}-{platform_tag}")

        analysis["wheel_types"] = list(analysis["wheel_types"])
        return analysis

    def analyze_build_complexity(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze package complexity to determine build requirements.

        Returns:
            Dictionary with build complexity analysis
        """
        info = metadata.get("info", {})

        analysis = {
            "likely_needs_compilation": False,
            "has_native_dependencies": False,
            "complexity_score": 0,
            "indicators": [],
        }

        # Check classifiers for compilation indicators
        classifiers = info.get("classifiers", [])
        compilation_indicators = [
            "Programming Language :: C",
            "Programming Language :: C++",
            "Programming Language :: Cython",
            "Programming Language :: Rust",
            "Programming Language :: Fortran",
        ]

        for classifier in classifiers:
            for indicator in compilation_indicators:
                if indicator in classifier:
                    analysis["likely_needs_compilation"] = True
                    analysis["indicators"].append(f"Classifier: {classifier}")
                    analysis["complexity_score"] += 2

        # Check keywords and description for build complexity indicators
        keywords = (info.get("keywords") or "").lower()
        description = (info.get("description") or "").lower()
        summary = (info.get("summary") or "").lower()

        complexity_keywords = [
            "cuda",
            "gpu",
            "accelerated",
            "native",
            "cython",
            "extension",
            "compiled",
            "binary",
            "fortran",
            "blas",
            "lapack",
            "mkl",
            "opencv",
            "tensorflow",
            "pytorch",
            "torch",
            "numpy",
        ]

        text_to_check = f"{keywords} {description} {summary}"
        for keyword in complexity_keywords:
            if keyword in text_to_check:
                analysis["indicators"].append(f"Keyword: {keyword}")
                analysis["complexity_score"] += 1

        # Check if package name suggests complexity
        package_name = (info.get("name") or "").lower()
        complex_packages = [
            "torch",
            "tensorflow",
            "numpy",
            "scipy",
            "opencv",
            "pillow",
            "lxml",
            "psycopg2",
            "mysqlclient",
            "cryptography",
        ]

        for complex_pkg in complex_packages:
            if complex_pkg in package_name:
                analysis["likely_needs_compilation"] = True
                analysis["indicators"].append(f"Known complex package: {package_name}")
                analysis["complexity_score"] += 3

        # Determine final assessment
        if analysis["complexity_score"] >= 3:
            analysis["likely_needs_compilation"] = True

        return analysis

    def process_package_info(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Process and structure package metadata for analysis.

        Args:
            metadata: Raw PyPI metadata

        Returns:
            Structured package information
        """
        info = metadata.get("info", {})

        # Basic package information
        package_info = {
            "name": info.get("name"),
            "version": info.get("version"),
            "summary": self.truncate_text(info.get("summary", "")),
            "description_content_type": info.get("description_content_type"),
            "author": info.get("author"),
            "author_email": info.get("author_email"),
            "maintainer": info.get("maintainer"),
            "maintainer_email": info.get("maintainer_email"),
            "license": info.get("license"),
            "keywords": info.get("keywords"),
            "classifiers": info.get("classifiers", []),
        }

        # License analysis
        package_info["license_classifiers"] = self.extract_license_classifiers(
            info.get("classifiers", [])
        )

        # Project URLs
        project_urls = info.get("project_urls", {})
        if project_urls:
            normalized_urls = {}
            for label, url in project_urls.items():
                normalized_label = self.normalize_url_label(label)
                normalized_urls[normalized_label] = url
            package_info["project_urls"] = normalized_urls
        else:
            # Fallback to homepage
            homepage = info.get("home_page")
            if homepage:
                package_info["project_urls"] = {"Homepage": homepage}

        # Requirements analysis
        package_info["requires_dist"] = info.get("requires_dist", [])
        package_info["requires_python"] = info.get("requires_python")

        # Distribution analysis
        package_info["distribution_analysis"] = (
            self.analyze_current_version_distributions(metadata)
        )

        # Build complexity analysis
        package_info["build_analysis"] = self.analyze_build_complexity(metadata)

        return package_info

    def format_output(self, package_info: dict[str, Any]) -> str:
        """Format package information for display."""
        output_lines = []

        # Header
        name = package_info.get("name", "Unknown")
        version = package_info.get("version", "Unknown")
        output_lines.append(f"Package: {name} {version}")
        output_lines.append("=" * 50)

        # Basic info
        if package_info.get("summary"):
            output_lines.append(f"Summary: {package_info['summary']}")

        if package_info.get("author"):
            output_lines.append(f"Author: {package_info['author']}")

        if package_info.get("license"):
            license_text = package_info["license"]
            # Truncate very long license text
            if len(license_text) > 200:
                license_text = license_text[:200] + "... (truncated)"
            output_lines.append(f"License: {license_text}")
        elif package_info.get("license_classifiers"):
            licenses = ", ".join(package_info["license_classifiers"])
            output_lines.append(f"License (from classifiers): {licenses}")

        # Python requirements
        if package_info.get("requires_python"):
            output_lines.append(f"Requires Python: {package_info['requires_python']}")

        # URLs
        project_urls = package_info.get("project_urls", {})
        if project_urls:
            output_lines.append("\nProject URLs:")
            for label, url in project_urls.items():
                output_lines.append(f"  {label}: {url}")

        # Distribution analysis
        dist_analysis = package_info.get("distribution_analysis", {})
        output_lines.append("\nDistribution Analysis:")
        output_lines.append(
            f"  Has source distribution: {dist_analysis.get('has_sdist', False)}"
        )
        output_lines.append(f"  Has wheels: {dist_analysis.get('has_wheels', False)}")

        wheel_types = dist_analysis.get("wheel_types", [])
        if wheel_types:
            output_lines.append(
                f"  Wheel types: {', '.join(wheel_types[:5])}"
            )  # Show first 5

        # Build analysis
        build_analysis = package_info.get("build_analysis", {})
        output_lines.append("\nBuild Complexity Analysis:")
        output_lines.append(
            f"  Likely needs compilation: {build_analysis.get('likely_needs_compilation', False)}"
        )
        output_lines.append(
            f"  Complexity score: {build_analysis.get('complexity_score', 0)}"
        )

        indicators = build_analysis.get("indicators", [])
        if indicators:
            output_lines.append("  Complexity indicators:")
            for indicator in indicators[:5]:  # Show first 5
                output_lines.append(f"    - {indicator}")

        # Dependencies
        requires_dist = package_info.get("requires_dist", [])
        if requires_dist:
            output_lines.append(f"\nDependencies ({len(requires_dist)}):")
            for dep in requires_dist:  # Show all dependencies
                output_lines.append(f"  - {dep}")

        return "\n".join(output_lines)

    def inspect_package(self, package_name: str, version: str | None = None) -> str:
        """
        Main method to inspect a package and return formatted output.

        Args:
            package_name: Name of the package to inspect
            version: Optional specific version

        Returns:
            Formatted package information string
        """
        try:
            metadata = self.get_package_metadata(package_name, version)
            package_info = self.process_package_info(metadata)
            return self.format_output(package_info)
        except Exception as e:
            logger.error(f"Failed to inspect package {package_name}: {e}")
            raise


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Inspect Python packages on PyPI for wheels builder compatibility analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s torch
  %(prog)s torch 2.7.1
  %(prog)s numpy --pypi-url https://custom.pypi.org/pypi
  %(prog)s --verbose tensorflow
        """,
    )

    parser.add_argument("package_name", help="Name of the package to inspect")

    parser.add_argument(
        "version",
        nargs="?",
        help="Optional specific version to inspect (if not provided, uses latest)",
    )

    parser.add_argument(
        "--pypi-url",
        default="https://pypi.org/pypi",
        help="PyPI base URL (default: https://pypi.org/pypi)",
    )

    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON instead of formatted text"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    inspector = PyPIInspector(args.pypi_url)

    try:
        if args.json:
            # Output raw structured data as JSON
            metadata = inspector.get_package_metadata(args.package_name, args.version)
            package_info = inspector.process_package_info(metadata)
            print(json.dumps(package_info, indent=2, default=str))
        else:
            # Output formatted text
            result = inspector.inspect_package(args.package_name, args.version)
            print(result)

    except PackageNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
