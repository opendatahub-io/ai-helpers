#!/usr/bin/env python3
"""Run Vale, asciidoctor, lychee, and YAML syntax checks on AsciiDoc files.

Collects results into structured JSON written to stdout.

Usage:
    python3 validate-artifacts.py <file1.adoc> [file2.adoc ...]
    python3 validate-artifacts.py modules/**/*.adoc

Output (JSON to stdout):
{
    "vale": { "status": "pass|fail|skipped", "findings": [...] },
    "asciidoctor": { "status": "pass|fail|skipped", "findings": [...] },
    "lychee": { "status": "pass|fail|skipped", "findings": [...] },
    "yaml_syntax": { "status": "pass|fail|skipped", "findings": [...] }
}
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def _load_dotenv() -> None:
    """Load .env file from project root if it exists. Existing env vars take precedence."""
    script_dir = Path(__file__).resolve().parent
    try:
        repo_root = subprocess.run(
            ["git", "-C", str(script_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except FileNotFoundError:
        repo_root = ""
    env_dir = Path(repo_root) if repo_root else Path.cwd()
    env_path = env_dir / ".env"
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key not in os.environ:
                os.environ[key] = value


_load_dotenv()

TOOL_TIMEOUT = 120  # seconds per external tool invocation


def _skipped_result() -> dict:
    return {"status": "skipped", "findings": []}


def _empty_results() -> dict:
    return {
        "vale": _skipped_result(),
        "asciidoctor": _skipped_result(),
        "lychee": _skipped_result(),
        "yaml_syntax": _skipped_result(),
    }


def run_vale(files: list[str]) -> dict:
    """Run Vale style checker on all files."""
    vale_bin = shutil.which("vale")
    if not vale_bin:
        print("Warning: vale not found, skipping style checks", file=sys.stderr)
        return _skipped_result()

    try:
        result = subprocess.run(
            [vale_bin, "--output=JSON"] + files,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUT,
            check=False,
        )
        output = result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("Warning: vale timed out", file=sys.stderr)
        return _skipped_result()

    if not output or output == "null":
        return {"status": "pass", "findings": []}

    try:
        raw = json.loads(output)
    except json.JSONDecodeError:
        return {"status": "pass", "findings": []}

    findings = []
    severity_map = {"error": "high", "warning": "medium"}
    for filepath, issues in raw.items():
        for issue in issues:
            findings.append(
                {
                    "file": filepath,
                    "line": issue.get("Line"),
                    "severity": severity_map.get(issue.get("Severity", ""), "low"),
                    "rule": issue.get("Check", ""),
                    "message": issue.get("Message", ""),
                    "tool": "vale",
                }
            )

    status = "fail" if findings else "pass"
    return {"status": status, "findings": findings}


def run_asciidoctor(files: list[str]) -> dict:
    """Run asciidoctor compilation check on .adoc files."""
    adoc_bin = shutil.which("asciidoctor")
    if not adoc_bin:
        print("Warning: asciidoctor not found, skipping compilation checks", file=sys.stderr)
        return _skipped_result()

    findings = []
    for filepath in files:
        if not filepath.endswith(".adoc"):
            continue
        try:
            result = subprocess.run(
                [adoc_bin, "-o", "/dev/null", "-v", filepath],
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT,
                check=False,
            )
            errors = result.stderr.strip()
        except subprocess.TimeoutExpired:
            errors = f"asciidoctor timed out on {filepath}"

        if errors:
            for line in errors.splitlines():
                if line.strip():
                    findings.append(
                        {
                            "file": filepath,
                            "message": line.strip(),
                            "severity": "medium",
                            "tool": "asciidoctor",
                        }
                    )

    status = "fail" if findings else "pass"
    return {"status": status, "findings": findings}


def run_lychee(files: list[str]) -> dict:
    """Run lychee link checker on files."""
    lychee_bin = shutil.which("lychee")
    if not lychee_bin:
        print("Warning: lychee not found, skipping link checks", file=sys.stderr)
        return _skipped_result()

    findings = []
    for filepath in files:
        try:
            result = subprocess.run(
                [lychee_bin, "--format", "json", filepath],
                capture_output=True,
                text=True,
                timeout=TOOL_TIMEOUT,
                check=False,
            )
            output = result.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"Warning: lychee timed out on {filepath}", file=sys.stderr)
            continue

        if not output:
            continue

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            continue

        failed = data.get("fail", [])
        for link in failed:
            link_str = link if isinstance(link, str) else str(link)
            findings.append(
                {
                    "file": filepath,
                    "message": f"Broken link: {link_str}",
                    "severity": "medium",
                    "tool": "lychee",
                }
            )

    status = "fail" if findings else "pass"
    return {"status": status, "findings": findings}


def run_yaml_syntax(files: list[str]) -> dict:
    """Validate YAML blocks embedded in AsciiDoc files."""
    findings = []
    source_yaml_re = re.compile(r"\[source,\s*yaml[^\]]*\]", re.IGNORECASE)

    for filepath in files:
        if not filepath.endswith(".adoc"):
            continue

        try:
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            continue

        in_yaml = False
        yaml_block_lines: list[str] = []
        yaml_delim = ""
        block_start = 0
        prev_line = ""

        for line_num, line in enumerate(lines, start=1):
            stripped = line.rstrip("\n")

            if in_yaml:
                if stripped == yaml_delim:
                    # End of block -- validate accumulated YAML
                    in_yaml = False
                    yaml_text = "".join(yaml_block_lines)
                    if yaml_text.strip():
                        try:
                            yaml.safe_load(yaml_text)
                        except yaml.YAMLError:
                            findings.append(
                                {
                                    "file": filepath,
                                    "line": block_start,
                                    "message": "Invalid YAML syntax in code block",
                                    "severity": "high",
                                    "tool": "yaml_syntax",
                                }
                            )
                    yaml_block_lines = []
                    yaml_delim = ""
                else:
                    yaml_block_lines.append(line)
            elif stripped in ("----", "===="):
                if source_yaml_re.search(prev_line):
                    in_yaml = True
                    yaml_delim = stripped
                    block_start = line_num

            prev_line = stripped

    status = "fail" if findings else "pass"
    return {"status": status, "findings": findings}


def main() -> None:
    files = sys.argv[1:]

    if not files:
        print('{"error": "No files specified"}', file=sys.stderr)
        print(json.dumps(_empty_results(), indent=2))
        return

    results = {}
    results["vale"] = run_vale(files)
    results["asciidoctor"] = run_asciidoctor(files)
    results["lychee"] = run_lychee(files)
    results["yaml_syntax"] = run_yaml_syntax(files)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
