#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "requests>=2.28.0",
# ]
# ///
"""
AI code review comment manager.

Post, update, and display AI-generated code review results on GitLab MRs.

Subcommands:
  post     Post review as inline comments + summary to a GitLab MR
  display  Display review results in the terminal

Environment variables (for 'post' with GitLab):
  GITLAB_API_TOKEN              GitLab Personal Access Token (required)
  CI_SERVER_URL                 GitLab server URL (default: https://gitlab.com)
  CI_PROJECT_ID                 GitLab project ID (required)
  CI_MERGE_REQUEST_IID          MR IID (required)
  CI_MERGE_REQUEST_DIFF_BASE_SHA  Base SHA for diff (required)
  CI_COMMIT_SHA                 Head SHA (required)
  CI_JOB_NAME                   Job name for footer (optional)
  CI_JOB_URL                    Job URL for footer (optional)
  CHILL_MODE                    Filter suggestion-level comments (default: true)
  VERBOSE                       Enable verbose output (default: false)

Usage:
  review.py post review.json [--chill|--no-chill] [--verbose]
  review.py display review.json [--chill|--no-chill]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

AI_REVIEW_MARKER = "<!-- ai-review"

SEVERITY_ICONS = {
    "critical": "\U0001f534",
    "major": "\U0001f7e0",
    "minor": "\U0001f7e1",
    "suggestion": "\U0001f4a1",
}

SEVERITY_ORDER = ["critical", "major", "minor", "suggestion"]
_VALID_SEVERITIES = frozenset(SEVERITY_ORDER)
_API_TIMEOUT = 30

_RED = "\033[0;31m"
_GREEN = "\033[0;32m"
_YELLOW = "\033[1;33m"
_BLUE = "\033[0;34m"
_CYAN = "\033[0;36m"
_NC = "\033[0m"


def _step(msg: str) -> None:
    print(f"{_BLUE}▶ {msg}{_NC}", file=sys.stderr)


def _success(msg: str) -> None:
    print(f"{_GREEN}✓ {msg}{_NC}", file=sys.stderr)


def _warning(msg: str) -> None:
    print(f"{_YELLOW}⚠ {msg}{_NC}", file=sys.stderr)


def _error(msg: str) -> None:
    print(f"{_RED}✗ {msg}{_NC}", file=sys.stderr)


def _header(msg: str) -> None:
    print(f"{_CYAN}{msg}{_NC}")


# ---------------------------------------------------------------------------
# JSON parsing (platform-independent)
# ---------------------------------------------------------------------------


def parse_review_json(filepath: str, chill_mode: bool = True) -> dict[str, Any]:
    """Parse, validate, and optionally filter review JSON from a file."""
    raw = Path(filepath).read_text(encoding="utf-8", errors="replace").strip()

    m = re.search(r"`{3,}(?:json)?\s*\n(.+?)\s*`{3,}", raw, re.DOTALL)
    if m:
        raw = m.group(1).strip()

    data = json.loads(raw)

    for field in ("summary", "inline_comments"):
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(data["inline_comments"], list):
        raise ValueError("inline_comments must be an array")

    for i, c in enumerate(data["inline_comments"]):
        for req in ("file", "line", "severity", "comment"):
            if req not in c:
                raise ValueError(f"inline_comments[{i}] missing field: {req}")
        if not isinstance(c["file"], str):
            raise ValueError(
                f"inline_comments[{i}].file: expected str, got {type(c['file']).__name__}"
            )
        if not isinstance(c["line"], int) or isinstance(c["line"], bool):
            raise ValueError(f"inline_comments[{i}].line: expected positive int, got {c['line']!r}")
        if c["line"] <= 0:
            raise ValueError(f"inline_comments[{i}].line: expected positive int, got {c['line']}")
        if not isinstance(c["comment"], str):
            raise ValueError(
                f"inline_comments[{i}].comment: expected str, got {type(c['comment']).__name__}"
            )
        sev = c["severity"]
        if sev not in _VALID_SEVERITIES:
            raise ValueError(
                f"inline_comments[{i}].severity: expected one of "
                f"{sorted(_VALID_SEVERITIES)}, got {sev!r}"
            )

    if chill_mode:
        before = len(data["inline_comments"])
        data["inline_comments"] = [
            c for c in data["inline_comments"] if c.get("severity") != "suggestion"
        ]
        filtered = before - len(data["inline_comments"])
        if filtered > 0:
            _step(f"Chill mode: filtered out {filtered} suggestion(s)")

    return data


# ---------------------------------------------------------------------------
# Dedup filtering (platform-independent)
# ---------------------------------------------------------------------------


def filter_already_reviewed(
    data: dict[str, Any], previous_sha: str, head_sha: str
) -> dict[str, Any]:
    """Remove comments on code unchanged since the previous review."""
    if previous_sha == head_sha:
        return data

    inline = data.get("inline_comments", [])
    if not inline:
        return data

    try:
        subprocess.check_output(
            ["git", "rev-parse", "--verify", previous_sha],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        _warning("Dedup filter: previous SHA not reachable, keeping all comments")
        return data

    try:
        diff_output = subprocess.check_output(
            ["git", "diff", f"{previous_sha}..{head_sha}", "--unified=0"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        _warning("Dedup filter: git diff failed, keeping all comments")
        return data

    changed_lines: dict[str, set[int]] = {}
    current_file: str | None = None
    for line in diff_output.split("\n"):
        file_match = re.match(r"^\+\+\+ b/(.+)$", line)
        if file_match:
            current_file = file_match.group(1)
            if current_file not in changed_lines:
                changed_lines[current_file] = set()
            continue
        hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if hunk_match and current_file:
            start = int(hunk_match.group(1))
            count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
            if count == 0:
                continue
            for i in range(start, start + count):
                changed_lines[current_file].add(i)

    filtered_comments = []
    skipped = 0
    for c in inline:
        fp = c.get("file", "")
        ln = c.get("line", 0)
        if fp in changed_lines and ln in changed_lines[fp]:
            filtered_comments.append(c)
        else:
            skipped += 1

    if skipped > 0:
        _step(f"Dedup filter: skipped {skipped} comment(s) on unchanged code")

    data["inline_comments"] = filtered_comments
    return data


# ---------------------------------------------------------------------------
# Display (platform-independent)
# ---------------------------------------------------------------------------


def _display_review(data: dict[str, Any]) -> None:
    """Display review results in the terminal."""
    ruler = "━" * 90
    print()
    _header(ruler)
    _header("                                   AI CODE REVIEW                                    ")
    _header(ruler)
    print()

    print("## Summary")
    print(data.get("summary", "No summary provided."))
    print()

    positives = data.get("positive_aspects", [])
    if positives:
        print("## Positive Aspects")
        for p in positives:
            print(f"  + {p}")
        print()

    inline = data.get("inline_comments", [])
    if inline:
        print(f"## Issues Found ({len(inline)})")
        print()
        for c in inline:
            icon = SEVERITY_ICONS.get(c["severity"], "\U0001f4ac")
            print(f"  {icon} [{c['severity'].upper()}] {c['file']}:{c['line']}")
            for ln in c["comment"].split("\n"):
                print(f"     {ln}")
            print()

    fix_prompt = data.get("fix_prompt")
    if fix_prompt:
        print("## Fix Prompt")
        print(fix_prompt)
        print()

    _header(ruler)
    print()


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------


def _detect_platform() -> str:
    """Detect the CI platform from environment variables.

    Returns 'gitlab', 'github', or 'local'.
    """
    if os.environ.get("CI_MERGE_REQUEST_IID") and os.environ.get("CI"):
        return "gitlab"
    if (
        os.environ.get("GITHUB_PULL_REQUEST_NUMBER")
        or os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
    ):
        return "github"
    return "local"


# ===========================================================================
# GitLab backend
# ===========================================================================


class _SafeSession(requests.Session):
    """Session with default timeout and SSRF-hardening (no redirect following).

    Redirects are blocked so the PRIVATE-TOKEN header is never forwarded
    to an unexpected host.  All requests get a default timeout to prevent
    indefinite hangs in CI.
    """

    def request(self, *args: Any, **kwargs: Any) -> requests.Response:  # type: ignore[override]
        kwargs.setdefault("timeout", _API_TIMEOUT)
        kwargs.setdefault("allow_redirects", False)
        return super().request(*args, **kwargs)


def _gitlab_paginated_get(session: requests.Session, url: str) -> list[Any]:
    """Fetch all pages from a GitLab list endpoint.

    Raises requests.HTTPError on auth/server errors (401, 403, 5xx).
    Returns an empty list on 404.
    """
    results: list[Any] = []
    params: dict[str, int] = {"per_page": 100}
    first_page = True
    while True:
        resp = session.get(url, params=params)
        if resp.status_code == 404:
            return results
        if resp.status_code != 200:
            if first_page:
                resp.raise_for_status()
            _warning(f"GitLab API returned HTTP {resp.status_code} during pagination")
            break
        page_data = resp.json()
        if not page_data:
            break
        results.extend(page_data)
        first_page = False
        next_page = resp.headers.get("x-next-page")
        if not next_page:
            break
        params["page"] = int(next_page)
    return results


def _make_review_marker(sha: str | None = None) -> str:
    if sha:
        return f"<!-- ai-review sha:{sha} -->"
    return "<!-- ai-review -->"


_LEGACY_EMOJI_PATTERN = re.compile(
    r"^[\U0001f534\U0001f7e0\U0001f7e1\U0001f4a1\U0001f4ac]"
    r"\s+\*\*(?:Critical|Major|Minor|Suggestion)\*\*:"
)


def _is_ai_review_comment(body: str, *, allow_legacy_cleanup: bool = False) -> bool:
    """Check whether a note body is an AI review comment.

    Returns True only when AI_REVIEW_MARKER is present, unless
    allow_legacy_cleanup is set, in which case the old emoji+severity
    pattern is also accepted (for cleaning up older reviews that
    predate the marker convention).
    """
    if AI_REVIEW_MARKER in body:
        return True
    if allow_legacy_cleanup and _LEGACY_EMOJI_PATTERN.match(body):
        return True
    return False


def _gitlab_get_previous_review_sha(session: requests.Session, api_base: str) -> str | None:
    """Extract commit SHA from the previous AI review summary note."""
    for note in _gitlab_paginated_get(session, f"{api_base}/notes"):
        if note.get("position") is not None:
            continue
        body = note.get("body", "")
        m = re.search(r"<!-- ai-review sha:([0-9a-f]+) -->", body)
        if m:
            return m.group(1)

    return None


def _gitlab_find_summary_note_id(session: requests.Session, api_base: str) -> int | None:
    """Find existing AI review summary note ID."""
    for note in _gitlab_paginated_get(session, f"{api_base}/notes"):
        if note.get("position") is not None:
            continue
        body = note.get("body", "")
        if (
            AI_REVIEW_MARKER in body
            or "## AI Code Review Summary" in body
            or "*Generated by [Claude Code AI Review]" in body
        ):
            return note["id"]

    return None


def _gitlab_delete_previous_discussions(
    session: requests.Session, api_base: str, *, verbose: bool = False
) -> None:
    """Delete previous AI review inline discussions on the MR."""
    _step("Checking for previous AI review discussions to delete...")

    discussions = _gitlab_paginated_get(session, f"{api_base}/discussions")
    if not discussions:
        _step("No previous AI review discussions found")
        return

    to_delete: list[tuple[str, int]] = []
    skipped = 0

    for d in discussions:
        notes = d.get("notes", [])
        if not notes:
            continue
        first_note = notes[0]
        if first_note.get("position") is None:
            continue
        body = first_note.get("body", "")
        if not _is_ai_review_comment(body):
            continue
        human_replies = [
            n
            for n in notes[1:]
            if not n.get("system", False) and AI_REVIEW_MARKER not in n.get("body", "")
        ]
        if human_replies:
            skipped += 1
            continue
        to_delete.append((d["id"], first_note["id"]))

    if not to_delete:
        if skipped:
            _step(f"Keeping {skipped} discussion(s) with human replies")
        else:
            _step("No previous AI review discussions found")
        return

    _step(f"Deleting {len(to_delete)} previous AI review discussion(s)...")
    if skipped:
        _step(f"Keeping {skipped} discussion(s) with human replies")

    deleted = 0
    for disc_id, note_id in to_delete:
        resp = session.delete(f"{api_base}/discussions/{disc_id}/notes/{note_id}")
        if 200 <= resp.status_code < 300:
            deleted += 1
        else:
            _warning(f"Failed to delete discussion {disc_id} (HTTP {resp.status_code})")

    _success(f"Deleted {deleted}/{len(to_delete)} previous discussion(s)")


def _gitlab_resolve_old_path(base_sha: str, head_sha: str, new_path: str) -> str:
    """Find the pre-rename path of a file, if it was renamed between base and head."""
    try:
        output = subprocess.check_output(
            ["git", "diff", "--diff-filter=R", "--name-status", f"{base_sha}..{head_sha}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return new_path
    for diff_line in output.strip().split("\n"):
        parts = diff_line.split("\t")
        if len(parts) >= 3 and parts[2] == new_path:
            return parts[1]
    return new_path


def _gitlab_post_inline_comment(
    session: requests.Session,
    api_base: str,
    file_path: str,
    line: int,
    comment: str,
    base_sha: str,
    head_sha: str,
    start_sha: str,
    *,
    verbose: bool = False,
) -> bool:
    """Post an inline discussion on the MR diff."""
    old_path = _gitlab_resolve_old_path(base_sha, head_sha, file_path)
    payload = {
        "body": comment,
        "position": {
            "base_sha": base_sha,
            "head_sha": head_sha,
            "start_sha": start_sha,
            "position_type": "text",
            "old_path": old_path,
            "new_path": file_path,
            "new_line": line,
        },
    }

    resp = session.post(f"{api_base}/discussions", json=payload)
    if 200 <= resp.status_code < 300:
        return True

    _warning(f"Failed to post inline comment on {file_path}:{line} (HTTP {resp.status_code})")
    if verbose:
        print(resp.text, file=sys.stderr)
    return False


def _gitlab_upsert_summary_note(
    session: requests.Session,
    api_base: str,
    body: str,
    *,
    verbose: bool = False,
) -> bool:
    """Delete existing summary note and post a new one."""
    existing_id = _gitlab_find_summary_note_id(session, api_base)
    if existing_id is not None:
        _step(f"Removing previous summary note (id: {existing_id})...")
        del_resp = session.delete(f"{api_base}/notes/{existing_id}")
        if not (200 <= del_resp.status_code < 300):
            _warning(f"Failed to delete previous summary note (HTTP {del_resp.status_code})")

    mr_iid = api_base.rsplit("/", 1)[-1]
    _step(f"Posting summary note to MR !{mr_iid}...")
    resp = session.post(f"{api_base}/notes", json={"body": body})
    if 200 <= resp.status_code < 300:
        return True

    _error(f"Failed to post summary note (HTTP {resp.status_code})")
    if verbose:
        print(resp.text, file=sys.stderr)
    return False


def _gitlab_build_summary_body(
    data: dict[str, Any],
    review_marker: str,
    job_name: str | None = None,
    job_url: str | None = None,
) -> str:
    """Build the markdown summary body for the MR note."""
    parts: list[str] = ["## AI Code Review Summary\n"]
    parts.append(data.get("summary", "No summary provided."))

    positives = data.get("positive_aspects", [])
    if positives:
        parts.append("\n### Positive Aspects")
        for p in positives:
            parts.append(f"- {p}")

    inline = data.get("inline_comments", [])
    if inline:
        severity_counts: dict[str, int] = {}
        for c in inline:
            s = c["severity"]
            severity_counts[s] = severity_counts.get(s, 0) + 1

        parts.append(f"\n### Issues Found ({len(inline)} total)")
        for sev in SEVERITY_ORDER:
            if sev in severity_counts:
                icon = SEVERITY_ICONS.get(sev, "")
                parts.append(f"- {icon} {sev.capitalize()}: {severity_counts[sev]}")
        parts.append("\n*See inline comments on the diff for details.*")

    fix_prompt = data.get("fix_prompt")
    if fix_prompt:
        parts.append("\n### \U0001f916 Fix all issues with AI agents")
        parts.append("\n**Copy-paste this into a prompt to automatically fix the issues found:**")
        parts.append(f"\n````\n{fix_prompt}\n````")

    summary = "\n".join(parts)

    jn = job_name or "ai-review"
    ju = job_url or "#"
    footer = (
        "\n\n---\n"
        "*Generated by [Claude Code AI Review]"
        "(https://gitlab.com/redhat/rhel-ai/agentic-ci/ai-agentic-lib)"
        f" • Job: [{jn}]({ju})*\n"
        f"{review_marker}"
    )

    return summary + footer


def _gitlab_post(args: argparse.Namespace) -> None:
    """Post review results to a GitLab MR."""
    token = os.environ.get("GITLAB_API_TOKEN")
    if not token:
        _error("GITLAB_API_TOKEN environment variable is required")
        sys.exit(1)

    project_id = os.environ.get("CI_PROJECT_ID")
    mr_iid = os.environ.get("CI_MERGE_REQUEST_IID")
    base_sha = os.environ.get("CI_MERGE_REQUEST_DIFF_BASE_SHA")
    head_sha = os.environ.get("CI_COMMIT_SHA")

    if not all([project_id, mr_iid, base_sha, head_sha]):
        _error(
            "Missing required CI variables: CI_PROJECT_ID, "
            "CI_MERGE_REQUEST_IID, CI_MERGE_REQUEST_DIFF_BASE_SHA, "
            "CI_COMMIT_SHA"
        )
        sys.exit(1)

    if not project_id.isdigit() or not mr_iid.isdigit():
        _error("CI_PROJECT_ID and CI_MERGE_REQUEST_IID must be numeric")
        sys.exit(1)

    gitlab_url = os.environ.get("CI_SERVER_URL", "https://gitlab.com").rstrip("/")
    start_sha = base_sha
    job_name = os.environ.get("CI_JOB_NAME")
    job_url = os.environ.get("CI_JOB_URL")
    verbose = _resolve_verbose(args)
    chill = _resolve_chill(args)

    try:
        data = parse_review_json(args.review_file, chill_mode=chill)
    except (json.JSONDecodeError, ValueError) as e:
        _error(f"Failed to parse review JSON: {e}")
        sys.exit(1)

    parsed_url = urlparse(gitlab_url)
    if parsed_url.scheme != "https":
        _error(f"CI_SERVER_URL must use HTTPS, got scheme: {parsed_url.scheme}")
        sys.exit(1)

    expected_host = os.environ.get("CI_SERVER_HOST")
    if expected_host and parsed_url.hostname != expected_host:
        _error(
            f"CI_SERVER_URL hostname ({parsed_url.hostname}) "
            f"does not match CI_SERVER_HOST ({expected_host})"
        )
        sys.exit(1)

    api_base = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
    session = _SafeSession()
    session.headers.update({"PRIVATE-TOKEN": token})

    review_marker = _make_review_marker(head_sha)

    try:
        prev_sha = _gitlab_get_previous_review_sha(session, api_base)
        if prev_sha and prev_sha != head_sha:
            _step(f"Found previous review (sha: {prev_sha[:8]}...), filtering unchanged code...")
            data = filter_already_reviewed(data, prev_sha, head_sha)

        inline = data.get("inline_comments", [])
        posted = 0
        failed = 0

        if inline:
            _step(f"Posting {len(inline)} inline comment(s) to MR !{mr_iid}...")
            for c in inline:
                icon = SEVERITY_ICONS.get(c["severity"], "\U0001f4ac")
                comment_body = (
                    f"{icon} **{c['severity'].capitalize()}**: {c['comment']}\n\n{review_marker}"
                )
                if _gitlab_post_inline_comment(
                    session,
                    api_base,
                    c["file"],
                    c["line"],
                    comment_body,
                    base_sha,
                    head_sha,
                    start_sha,
                    verbose=verbose,
                ):
                    posted += 1
                else:
                    failed += 1

            _success(f"Posted {posted}/{len(inline)} inline comments ({failed} failed)")
        else:
            _step("No inline comments to post")

        if failed == 0:
            _gitlab_delete_previous_discussions(session, api_base, verbose=verbose)
        else:
            _warning("Skipping deletion of previous discussions due to posting failures")

        summary_body = _gitlab_build_summary_body(data, review_marker, job_name, job_url)
        if _gitlab_upsert_summary_note(session, api_base, summary_body, verbose=verbose):
            _success(f"Summary posted to merge request !{mr_iid}")
        else:
            _error("Failed to post summary note")
            sys.exit(1)

        if failed > 0:
            _error(f"{failed}/{len(inline)} inline comments failed to post")
            sys.exit(1)
    except requests.exceptions.HTTPError as e:
        _error(f"GitLab API error: {e}")
        sys.exit(1)


# ===========================================================================
# GitHub backend (not yet implemented)
# ===========================================================================


def _github_post(args: argparse.Namespace) -> None:
    """Post review results to a GitHub PR (not yet implemented)."""
    _error("GitHub support is not yet implemented.")
    _error("Currently only GitLab is supported for posting reviews.")
    _error("Use 'display' to view review results locally instead.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def _resolve_chill(args: argparse.Namespace) -> bool:
    """Resolve chill mode: CLI flag > env var > default True."""
    if args.chill is not None:
        return args.chill
    return os.environ.get("CHILL_MODE", "true").lower() == "true"


def _resolve_verbose(args: argparse.Namespace) -> bool:
    """Resolve verbose: CLI flag > env var > default False."""
    if getattr(args, "verbose", False):
        return True
    return os.environ.get("VERBOSE", "false").lower() == "true"


def cmd_post(args: argparse.Namespace) -> None:
    """Post review results to the detected platform.

    Falls back to terminal display when no CI platform is detected.
    """
    platform = _detect_platform()

    if platform == "gitlab":
        _gitlab_post(args)
    elif platform == "github":
        _github_post(args)
    else:
        _step("No CI platform detected — displaying review locally.")
        cmd_display(args)


def cmd_display(args: argparse.Namespace) -> None:
    """Display review results in terminal."""
    chill = _resolve_chill(args)

    try:
        data = parse_review_json(args.review_file, chill_mode=chill)
    except (json.JSONDecodeError, ValueError) as e:
        _error(f"Failed to parse review JSON: {e}")
        sys.exit(1)

    _display_review(data)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("review_file", help="Path to the review JSON file")
    chill_group = parser.add_mutually_exclusive_group()
    chill_group.add_argument(
        "--chill",
        action="store_true",
        default=None,
        dest="chill",
        help="Filter out suggestion-level comments (default)",
    )
    chill_group.add_argument(
        "--no-chill",
        action="store_false",
        dest="chill",
        help="Include suggestion-level comments",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI code review comment manager.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    post_parser = subparsers.add_parser("post", help="Post review to GitLab MR")
    _add_common_args(post_parser)
    post_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    post_parser.set_defaults(func=cmd_post)

    display_parser = subparsers.add_parser("display", help="Display review in terminal")
    _add_common_args(display_parser)
    display_parser.set_defaults(func=cmd_display)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
