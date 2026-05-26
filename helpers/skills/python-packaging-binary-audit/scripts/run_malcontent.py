#!/usr/bin/env python3
"""Run malcontent (mal) analysis on a directory of binary files.

Expects the ``mal`` binary to be available on PATH or specified via
the ``MALCONTENT_BIN`` environment variable.  The pipeline CI job is
responsible for installing malcontent before invoking this skill
(see AIPCC-16968).

Usage:
    ./scripts/run_malcontent.py <directory>
    ./scripts/run_malcontent.py /path/to/staged/binaries

Exit codes:
    0 — analysis completed successfully (JSON on stdout)
    1 — runtime error (invalid input, timeout, bad JSON output, exec failure)
    2 — malcontent binary is not installed / not found
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys

MALCONTENT_TIMEOUT = int(os.environ.get("MALCONTENT_TIMEOUT", "600"))


def _find_malcontent_binary() -> str | None:
    """Locate the malcontent binary, verifying it is executable."""
    explicit = os.environ.get("MALCONTENT_BIN")
    if explicit:
        path = pathlib.Path(explicit)
        if path.is_file() and os.access(path, os.X_OK):
            return explicit
    found = shutil.which("mal")
    if found and os.access(found, os.X_OK):
        return found
    return None


def run_malcontent(target_dir: pathlib.Path) -> dict | str:
    """Run malcontent analysis via the native ``mal`` binary.

    Returns the parsed JSON dict on success, or a status string on failure:
    ``"unavailable"`` if the binary is not found, ``"timeout"`` on timeout,
    ``"invalid"`` if output is not valid JSON, ``"failed"`` for other errors.
    """
    mal_bin = _find_malcontent_binary()
    if not mal_bin:
        return "unavailable"

    cmd = [
        mal_bin,
        "analyze",
        str(target_dir),
        "--format",
        "json",
        "--min-risk",
        "medium",
    ]
    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=MALCONTENT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(
            f"ERROR: malcontent timed out after {MALCONTENT_TIMEOUT}s",
            file=sys.stderr,
        )
        return "timeout"
    except FileNotFoundError:
        print(f"ERROR: binary not found at {mal_bin}", file=sys.stderr)
        return "unavailable"
    except (PermissionError, OSError) as exc:
        print(f"ERROR: cannot execute {mal_bin}: {exc}", file=sys.stderr)
        return "failed"

    if result.returncode != 0 and not result.stdout.strip():
        msg = f"ERROR: malcontent exited {result.returncode}: {result.stderr[:500]}"
        print(msg, file=sys.stderr)
        return "failed"

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("ERROR: malcontent produced invalid JSON", file=sys.stderr)
        if result.stdout:
            print(f"First 500 chars: {result.stdout[:500]}", file=sys.stderr)
        return "invalid"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run malcontent analysis on a directory of binary files.",
    )
    parser.add_argument(
        "directory",
        help="Directory containing binary files to analyze",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Write JSON output to file (in addition to stdout)",
    )
    args = parser.parse_args()

    target = pathlib.Path(args.directory)
    if not target.is_dir():
        print(f"ERROR: {target} is not a directory", file=sys.stderr)
        return 1

    data = run_malcontent(target)

    if isinstance(data, str):
        exit_map = {"unavailable": 2, "timeout": 1, "invalid": 1, "failed": 1}
        if data == "unavailable":
            print(
                "ERROR: malcontent is not available. Install the 'mal' binary "
                "(see https://github.com/chainguard-dev/malcontent) or set "
                "MALCONTENT_BIN to point to the binary.",
                file=sys.stderr,
            )
        else:
            print(f"ERROR: malcontent {data}", file=sys.stderr)
        return exit_map.get(data, 1)

    print("malcontent analysis completed", file=sys.stderr)
    output = json.dumps(data, indent=2)
    print(output)

    if args.output:
        out_path = pathlib.Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
        print(f"Output written to {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
