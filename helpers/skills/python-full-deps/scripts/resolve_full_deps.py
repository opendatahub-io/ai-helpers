#!/usr/bin/env python3
"""
Resolve full dependency tree for a Python package (install-time deps only).

Uses ``uv pip compile`` when available; falls back to
``pip install --dry-run --report`` in a temporary venv.

Output: sorted, unique "name==version" lines (PEP 503 normalized names).

Note: the pip fallback cannot cross-resolve for a different Python version;
it resolves for whatever Python is running this script.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def normalize_name(name: str) -> str:
    """PEP 503: lowercase and collapse '-', '_', '.' to '-'."""
    return re.sub(r"[-_.]+", "-", name).lower()


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_compile_output(stdout: str) -> set[tuple[str, str]]:
    """Parse ``uv pip compile`` / requirements.txt style output."""
    deps: set[tuple[str, str]] = set()
    line_re = re.compile(r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*==\s*([^\s\[#]+)")
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        matched = line_re.match(line)
        if matched:
            deps.add((normalize_name(matched.group(1)), matched.group(2)))
    return deps


def parse_pip_report(report_json: str) -> set[tuple[str, str]]:
    """Parse ``pip install --dry-run --report`` JSON output."""
    data = json.loads(report_json)
    deps: set[tuple[str, str]] = set()
    for item in data.get("install", []):
        meta = item.get("metadata", {})
        name = meta.get("name", "")
        version = meta.get("version", "")
        if name and version:
            deps.add((normalize_name(name), version))
    return deps


# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------


def resolve_with_uv(req: str, python_version: str) -> set[tuple[str, str]]:
    """Resolve dependencies using ``uv pip compile``."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "requirements.txt"
        cmd = [
            "uv",
            "pip",
            "compile",
            "-",
            "--python-version",
            python_version,
            "-o",
            str(out_file),
        ]
        result = subprocess.run(
            cmd,
            input=req.encode(),
            capture_output=True,
            timeout=150,
        )
        if result.returncode != 0:
            raise RuntimeError(f"uv pip compile failed: {result.stderr.decode()}")
        return parse_compile_output(out_file.read_text())


def resolve_with_pip(req: str) -> set[tuple[str, str]]:
    """Fallback: resolve deps via ``pip install --dry-run --report`` in a temp venv."""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / "venv"
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
            timeout=60,
        )
        pip_bin = str(venv_dir / "bin" / "pip")

        # Ensure pip >= 22.2 (needed for --dry-run and --report)
        upgrade = subprocess.run(
            [pip_bin, "install", "--upgrade", "pip>=22.2"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if upgrade.returncode != 0:
            raise RuntimeError(
                f"failed to upgrade pip for --report support: {upgrade.stderr}"
            )

        report_file = Path(tmpdir) / "report.json"
        result = subprocess.run(
            [
                pip_bin,
                "install",
                "--dry-run",
                "--no-input",
                "--report",
                str(report_file),
                req,
            ],
            capture_output=True,
            timeout=150,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pip dry-run failed: {result.stderr.decode()}")
        return parse_pip_report(report_file.read_text())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: resolve_full_deps.py <package> [version] [python_version]",
            file=sys.stderr,
        )
        print("  package: PyPI name (required)", file=sys.stderr)
        print("  version: e.g. 0.4.0 (optional, default latest)", file=sys.stderr)
        print("  python_version: e.g. 3.12 (optional, default 3.12)", file=sys.stderr)
        return 1
    package = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].strip() else None
    python_version = sys.argv[3] if len(sys.argv) > 3 else "3.12"
    req = f"{package}=={version}" if version else package

    try:
        deps = resolve_with_uv(req, python_version)
    except FileNotFoundError:
        print("uv not found; falling back to pip --dry-run", file=sys.stderr)
        running_python = f"{sys.version_info.major}.{sys.version_info.minor}"
        if python_version != running_python:
            print(
                f"warning: pip fallback resolves for running Python {running_python}, "
                f"not requested --python-version {python_version}",
                file=sys.stderr,
            )
        try:
            deps = resolve_with_pip(req)
        except Exception as e:
            print(str(e), file=sys.stderr)
            return 1
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1

    for name, ver in sorted(deps):
        print(f"{name}=={ver}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
