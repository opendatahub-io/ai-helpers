#!/usr/bin/env python3
"""Fetch a Google Doc by ID and output its plain text content."""

import json
import subprocess
import sys


def run_gws(*args: str) -> dict:
    try:
        result = subprocess.run(["gws", *args], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        print(f"gws timed out after {e.timeout}s", file=sys.stderr)
        if stdout:
            print(f"stdout: {stdout.strip()}", file=sys.stderr)
        if stderr:
            print(f"stderr: {stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error running gws: {e}", file=sys.stderr)
        sys.exit(1)
    stdout = "\n".join(
        line for line in result.stdout.splitlines() if not line.startswith("Using keyring")
    ).strip()
    if result.returncode != 0:
        print(f"gws error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    if not stdout:
        print("gws returned no output", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(stdout)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Failed to parse gws output as JSON: {e}", file=sys.stderr)
        print(f"stdout: {stdout}", file=sys.stderr)
        if result.stderr.strip():
            print(f"stderr: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def extract_text(node: dict | list | str | None) -> list[str]:
    """Recursively collect textRun content from a Docs API response node."""
    texts: list[str] = []
    if isinstance(node, dict):
        if "textRun" in node:
            texts.append(node["textRun"].get("content", ""))
        for value in node.values():
            texts.extend(extract_text(value))
    elif isinstance(node, list):
        for item in node:
            texts.extend(extract_text(item))
    return texts


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: read_doc.py <doc-id>", file=sys.stderr)
        sys.exit(1)

    doc_id = sys.argv[1]
    data = run_gws(
        "docs",
        "documents",
        "get",
        "--params",
        json.dumps({"documentId": doc_id}),
    )
    text = "".join(extract_text(data.get("body", {})))
    if not text.strip():
        print("Document appears to be empty", file=sys.stderr)
        sys.exit(1)
    print(text)


if __name__ == "__main__":
    main()
