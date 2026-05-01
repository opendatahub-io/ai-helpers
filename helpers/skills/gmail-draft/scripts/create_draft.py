#!/usr/bin/env python3
"""Create a Gmail draft from a plain-text body file.

Uses `gws gmail +send --draft` which handles MIME encoding automatically.
"""

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to", required=True, help="Comma-separated recipient emails")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument(
        "--body-file",
        required=True,
        help="Path to a UTF-8 plain-text file containing the email body",
    )
    args = parser.parse_args()

    try:
        with open(args.body_file, encoding="utf-8") as f:
            body = f.read()
    except OSError as e:
        print(f"Error reading body file {args.body_file!r}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            [
                "gws",
                "gmail",
                "+send",
                "--to",
                args.to,
                "--subject",
                args.subject,
                "--body",
                body,
                "--draft",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
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
    print(stdout)


if __name__ == "__main__":
    main()
