#!/usr/bin/env python3
"""Scan a directory for compiled / binary files.

Replicates the detection logic from Fromager's ``scan_compiled_extensions``
(fromager/src/fromager/sources.py) using the same extension suffixes, ignore
suffixes, and magic-header bytes so that findings are directly comparable.

Usage:
    ./scripts/scan_binaries.py <directory>
    ./scripts/scan_binaries.py /path/to/cloned/repo

Output:
    JSON object on stdout with ``total``, ``findings``, and optionally
    ``staging_failures`` fields.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys

EXTENSION_SUFFIXES: set[str] = {".so", ".dylib", ".pyd", ".dll", ".exe"}

IGNORE_SUFFIXES: set[str] = {
    ".c",
    ".cc",
    ".css",
    ".cu",
    ".cuh",
    ".go",
    ".h",
    ".hip",
    ".hpp",
    ".html",
    ".ini",
    ".js",
    ".md",
    ".py",
    ".rs",
    ".rst",
    ".sh",
    ".ts",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

_MAGIC_NAMES: list[tuple[bytes, str]] = [
    (b"\x7fELF", "ELF"),  # ELF executable / shared object (Linux)
    (b"!<arch>\n", "ar_archive"),  # Unix ar archive (.a static library)
    (b"!<thin>\n", "thin_ar"),  # GNU thin archive
    (b"\xfe\xed\xfa\xcf", "MachO"),  # Mach-O 64-bit big-endian
    (b"\xfe\xed\xfa\xce", "MachO"),  # Mach-O 32-bit big-endian
    (b"\xcf\xfa\xed\xfe", "MachO"),  # Mach-O 64-bit little-endian
    (b"\xce\xfa\xed\xfe", "MachO"),  # Mach-O 32-bit little-endian
    (b"\xca\xfe\xba\xbe", "universal_or_java"),  # macOS universal binary or Java class
    (b"MZ", "PE_MZ"),  # PE/COFF executable (Windows)
]

_MAGIC_READ: int = max(len(h) for h, _ in _MAGIC_NAMES)


def _identify_magic(header: bytes) -> str | None:
    for prefix, name in _MAGIC_NAMES:
        if header.startswith(prefix):
            return name
    return None


def scan_directory(root_dir: pathlib.Path) -> dict:
    """Walk *root_dir* and return all files matching binary signatures."""
    findings: list[dict] = []

    for dirpath, _dirnames, filenames in os.walk(root_dir, followlinks=False):
        directory = pathlib.Path(dirpath)
        for filename in filenames:
            filepath = directory / filename
            suffix = filepath.suffix
            try:
                relpath = str(filepath.relative_to(root_dir))
            except ValueError:
                continue

            if suffix in EXTENSION_SUFFIXES:
                try:
                    size = filepath.stat().st_size
                except OSError:
                    size = 0
                findings.append(
                    {
                        "path": relpath,
                        "abs_path": str(filepath),
                        "match_type": "extension",
                        "suffix": suffix,
                        "size": size,
                    }
                )
            elif suffix not in IGNORE_SUFFIXES:
                try:
                    with filepath.open("rb") as f:
                        header = f.read(_MAGIC_READ)
                except (IsADirectoryError, FileNotFoundError, PermissionError, OSError):
                    continue

                magic_name = _identify_magic(header)
                if magic_name is not None:
                    try:
                        size = filepath.stat().st_size
                    except OSError:
                        size = 0
                    findings.append(
                        {
                            "path": relpath,
                            "abs_path": str(filepath),
                            "match_type": "magic_header",
                            "suffix": suffix or "(none)",
                            "size": size,
                            "magic": magic_name,
                        }
                    )

    return {"total": len(findings), "findings": findings}


def stage_binaries(findings: list[dict], staging_dir: pathlib.Path) -> tuple[pathlib.Path, int]:
    """Copy detected binaries into *staging_dir* for malcontent analysis."""
    resolved = staging_dir.resolve()
    if resolved in (pathlib.Path("/"), pathlib.Path.home()):
        raise ValueError(f"Refusing unsafe staging directory: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)

    failed_copies = 0
    for finding in findings:
        src = pathlib.Path(finding["abs_path"])
        dest = resolved / finding["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dest)
        except (FileNotFoundError, PermissionError, OSError) as exc:
            failed_copies += 1
            print(
                f"WARNING: failed to stage {src} -> {dest}: {exc}",
                file=sys.stderr,
            )

    if failed_copies:
        print(
            f"WARNING: {failed_copies} file(s) could not be staged",
            file=sys.stderr,
        )

    return resolved, failed_copies


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan a directory for compiled/binary files using Fromager-style detection.",
    )
    parser.add_argument("directory", help="Directory to scan for binary files")
    parser.add_argument(
        "--stage-to",
        metavar="DIR",
        help="Copy detected binaries to this staging directory (for malcontent analysis)",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.directory)
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 1

    result = scan_directory(root)

    if args.stage_to and result["findings"]:
        staging = pathlib.Path(args.stage_to)
        staged_dir, failed_copies = stage_binaries(result["findings"], staging)
        print(f"Staged {result['total']} binaries to {staged_dir}", file=sys.stderr)
        if failed_copies:
            result["staging_failures"] = failed_copies

    json.dump(result, sys.stdout, indent=2)
    print(file=sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
