#!/usr/bin/env python3
"""
Source repository finder for Python packages.

This script attempts to find the source repository for a given Python package
by checking PyPI metadata and using web search as fallback.
"""

import json
import re
import sys
import urllib.request
import urllib.error
from typing import Dict, Optional


class ConfidenceLevel:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceFinder:
    """Finds source repositories for Python packages."""

    def __init__(self):
        self.pypi_base_url = "https://pypi.org/pypi"

    def find_source_repository(self, package_name: str) -> Dict[str, str]:
        """
        Find the source repository for a Python package.

        Args:
            package_name: Name of the Python package

        Returns:
            Dictionary with 'url', 'confidence', and 'method' keys
        """
        # First try PyPI metadata
        result = self._check_pypi_metadata(package_name)
        if result:
            return result

        # If PyPI doesn't work, we'd need web search as fallback
        # For this implementation, we'll return a low confidence result
        return {
            "url": None,
            "confidence": ConfidenceLevel.LOW,
            "method": "pypi_fallback",
            "message": f"Could not find repository in PyPI metadata for '{package_name}'. Manual search recommended.",
        }

    def _check_pypi_metadata(self, package_name: str) -> Optional[Dict[str, str]]:
        """Check PyPI API for repository information."""
        try:
            url = f"{self.pypi_base_url}/{package_name}/json"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            # Extract project URLs from metadata
            project_urls = data.get("info", {}).get("project_urls", {}) or {}
            home_page = data.get("info", {}).get("home_page", "")

            # Look for repository URLs in order of preference
            repo_candidates = []

            # Check project_urls first
            for key, value in project_urls.items():
                if value and self._is_repository_url(value):
                    confidence = self._calculate_confidence_from_key(key)
                    repo_candidates.append((value, confidence, f"project_urls.{key}"))

            # Check homepage as backup
            if home_page and self._is_repository_url(home_page):
                repo_candidates.append((home_page, ConfidenceLevel.MEDIUM, "homepage"))

            # Return the best candidate
            if repo_candidates:
                best_candidate = max(
                    repo_candidates, key=lambda x: self._confidence_score(x[1])
                )
                url, confidence, source = best_candidate
                return {
                    "url": url,
                    "confidence": confidence,
                    "method": f"pypi_metadata_{source}",
                    "package_name": package_name,
                }

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {
                    "url": None,
                    "confidence": ConfidenceLevel.LOW,
                    "method": "pypi_not_found",
                    "message": f"Package '{package_name}' not found on PyPI",
                }
        except Exception as e:
            return {
                "url": None,
                "confidence": ConfidenceLevel.LOW,
                "method": "pypi_error",
                "message": f"Error accessing PyPI for '{package_name}': {str(e)}",
            }

        return None

    def _is_repository_url(self, url: str) -> bool:
        """Check if URL appears to be a code repository."""
        if not url:
            return False

        # Common repository hosting platforms
        repo_patterns = [
            r"github\.com/[^/]+/[^/]+",
            r"gitlab\.com/[^/]+/[^/]+",
            r"bitbucket\.org/[^/]+/[^/]+",
            r"git\.sr\.ht/[^/]+/[^/]+",
            r"codeberg\.org/[^/]+/[^/]+",
        ]

        url_lower = url.lower()
        for pattern in repo_patterns:
            if re.search(pattern, url_lower):
                return True

        return False

    def _calculate_confidence_from_key(self, key: str) -> str:
        """Calculate confidence level based on project_urls key name."""
        key_lower = key.lower()

        high_confidence_keys = [
            "repository",
            "source",
            "source code",
            "git",
            "github",
            "gitlab",
        ]
        medium_confidence_keys = ["homepage", "home", "website", "project"]

        for high_key in high_confidence_keys:
            if high_key in key_lower:
                return ConfidenceLevel.HIGH

        for medium_key in medium_confidence_keys:
            if medium_key in key_lower:
                return ConfidenceLevel.MEDIUM

        return ConfidenceLevel.LOW

    def _confidence_score(self, confidence: str) -> int:
        """Convert confidence level to numeric score for comparison."""
        scores = {
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.LOW: 1,
        }
        return scores.get(confidence, 0)


def main():
    """Command line interface for the source finder."""
    if len(sys.argv) != 2:
        print("Usage: python finder.py <package_name>")
        sys.exit(1)

    package_name = sys.argv[1]
    finder = SourceFinder()
    result = finder.find_source_repository(package_name)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
