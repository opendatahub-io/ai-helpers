#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///
"""
AIPCC Commit Message Validator

Validates commit messages against AIPCC linter rules used by Red Hat AI projects.
Mimics the JIRA ticket linter from:
https://gitlab.com/platform-engineering-org/gitlab-ci/-/blob/main/script/jira_ticket_linter.py

Usage:
    # Validate the last commit
    ./validate_commit.py

    # Validate a specific commit
    ./validate_commit.py <commit-sha>

    # Validate multiple commits (e.g., all commits on branch)
    ./validate_commit.py HEAD~3..HEAD

    # Validate commits on current branch vs main
    ./validate_commit.py origin/main..HEAD
"""

import re
import subprocess
import sys

# Valid JIRA project prefixes
JIRA_PATTERN = re.compile(r"^(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-\d+:")
SIGNED_OFF_BY_PATTERN = re.compile(r"Signed-off-by: .+ <.+@.+>")
TRAILER_PATTERN = re.compile(
    r"^(Signed-off-by|Co-authored-by|Co-Authored-By|Fixes|Closes): ", re.IGNORECASE
)


def get_commit_message(commit_ref: str = "HEAD") -> tuple[str, str]:
    """Get commit subject and body separately."""
    # Get subject (first line)
    subject = subprocess.run(
        ["git", "log", "-1", "--format=%s", commit_ref],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Get body (everything after first line)
    body = subprocess.run(
        ["git", "log", "-1", "--format=%b", commit_ref],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    return subject, body


def get_commits_in_range(range_spec: str) -> list[str]:
    """Get list of commit SHAs in a range."""
    result = subprocess.run(
        ["git", "rev-list", range_spec],
        capture_output=True,
        text=True,
        check=True,
    )
    return [sha for sha in result.stdout.strip().split("\n") if sha]


def validate_commit(commit_ref: str = "HEAD") -> tuple[bool, list[str]]:
    """
    Validate a commit message against AIPCC linter rules.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    try:
        subject, body = get_commit_message(commit_ref)
    except subprocess.CalledProcessError as e:
        return False, [f"Failed to get commit message: {e}"]

    # Get short SHA for error messages
    try:
        short_sha = subprocess.run(
            ["git", "rev-parse", "--short", commit_ref],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        short_sha = commit_ref[:12]

    # Rule 1: Subject must start with valid JIRA ticket
    if not JIRA_PATTERN.match(subject):
        errors.append(
            f"[{short_sha}] Subject must start with JIRA ticket "
            f"(RHELAI|RHOAIENG|AIPCC|INFERENG|RHAIENG)-XXXX:\n"
            f"  Got: {subject[:60]}..."
        )

    # Rule 2: Must have a body with at least one non-trailer line
    body_lines = [
        line
        for line in body.splitlines()
        if line.strip() and not TRAILER_PATTERN.match(line.strip())
    ]
    if not body_lines:
        errors.append(
            f"[{short_sha}] Commit must have a body (description after blank line)\n"
            f"  Trailer-only bodies (Signed-off-by, Co-authored-by) do not count"
        )

    # Rule 3: Must have Signed-off-by
    full_message = f"{subject}\n\n{body}"
    if not SIGNED_OFF_BY_PATTERN.search(full_message):
        errors.append(
            f"[{short_sha}] Commit must include 'Signed-off-by: Name <email@domain>'\n"
            f"  Use: git commit --signoff"
        )

    return len(errors) == 0, errors


def main():
    args = sys.argv[1:]

    # Determine what to validate
    if not args:
        # Default: validate HEAD
        commits = ["HEAD"]
    elif ".." in args[0]:
        # Range specified
        try:
            commits = get_commits_in_range(args[0])
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to resolve commit range '{args[0]}': {e.stderr.strip()}")
            return 1
    else:
        # Specific commit(s)
        commits = args

    if not commits:
        print("No commits to validate")
        return 0

    all_valid = True
    all_errors = []

    for commit in commits:
        is_valid, errors = validate_commit(commit)
        if not is_valid:
            all_valid = False
            all_errors.extend(errors)

    if all_valid:
        print(f"✓ All {len(commits)} commit(s) pass AIPCC linter validation")
        return 0
    else:
        print("✗ Commit validation failed:\n")
        for error in all_errors:
            print(f"  {error}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
