#!/usr/bin/env python3

"""
Pull Request Comment Analysis Script

Fetches comments from a GitHub PR using the gh CLI and outputs them in a structured JSON format
for further analysis by the Claude skill.

Requires: gh CLI (GitHub CLI) to be installed and authenticated
"""

import json
import subprocess
import sys
from typing import Dict, List, Any
from urllib.parse import urlparse


def parse_github_pr_url(url: str) -> Dict[str, str]:
    """
    Parse a GitHub PR URL and extract owner, repo, and PR number.

    Supports: https://github.com/owner/repo/pull/123
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')

    if 'github.com' in parsed.netloc:
        if len(path_parts) >= 4 and path_parts[2] == 'pull':
            return {
                'owner': path_parts[0],
                'repo': path_parts[1],
                'pr_number': path_parts[3],
            }

    raise ValueError(f"Unsupported or invalid GitHub PR URL format: {url}")


def run_gh_command(args: List[str]) -> str:
    """
    Run a gh CLI command and return the output.

    Args:
        args: Command arguments (without 'gh' prefix)

    Returns:
        Command output as string

    Raises:
        subprocess.CalledProcessError: If the command fails
    """
    try:
        result = subprocess.run(
            ['gh'] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"gh command failed: {error_msg}") from e
    except FileNotFoundError:
        raise RuntimeError(
            "gh CLI not found. Please install it from https://cli.github.com/ "
            "and authenticate with 'gh auth login'"
        )


def fetch_github_pr_comments(owner: str, repo: str, pr_number: str) -> List[Dict[str, Any]]:
    """
    Fetch comments from a GitHub pull request using gh CLI.

    Uses:
    - gh pr view <number> --repo <owner/repo> --json comments --json reviews
    """
    repo_full = f"{owner}/{repo}"

    # Fetch PR data including comments and reviews
    pr_data_json = run_gh_command([
        'pr', 'view', pr_number,
        '--repo', repo_full,
        '--json', 'comments,reviews,url'
    ])

    pr_data = json.loads(pr_data_json)

    comments = []

    # Process general PR comments (issue comments)
    for comment in pr_data.get('comments', []):
        comments.append({
            'id': comment.get('id', ''),
            'type': 'issue',
            'author': comment.get('author', {}).get('login', 'unknown'),
            'body': comment.get('body', ''),
            'path': '',
            'line': '',
            'created_at': comment.get('createdAt', ''),
            'url': comment.get('url', '')
        })

    # Process review comments
    for review in pr_data.get('reviews', []):
        review_author = review.get('author', {}).get('login', 'unknown')
        review_body = review.get('body', '')
        review_created = review.get('submittedAt', '')

        # Add top-level review comment if it has content
        if review_body and review_body.strip():
            comments.append({
                'id': review.get('id', ''),
                'type': 'review',
                'author': review_author,
                'body': review_body,
                'path': '',
                'line': '',
                'created_at': review_created,
                'url': pr_data.get('url', '') + '#pullrequestreview-' + str(review.get('id', ''))
            })

    # Fetch inline review comments separately
    # gh pr view <number> --repo <owner/repo> --json reviewThreads
    review_threads_json = run_gh_command([
        'pr', 'view', pr_number,
        '--repo', repo_full,
        '--json', 'reviewThreads'
    ])

    review_threads_data = json.loads(review_threads_json)

    # Process inline review comments
    for thread in review_threads_data.get('reviewThreads', []):
        path = thread.get('path', '')
        line = thread.get('line', '')

        for comment in thread.get('comments', []):
            comments.append({
                'id': comment.get('id', ''),
                'type': 'review',
                'author': comment.get('author', {}).get('login', 'unknown'),
                'body': comment.get('body', ''),
                'path': path,
                'line': line,
                'created_at': comment.get('createdAt', ''),
                'url': comment.get('url', '')
            })

    return comments


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Missing PR URL argument',
            'usage': 'analyze_pr_comments.py <pr_url>'
        }), file=sys.stderr)
        sys.exit(1)

    pr_url = sys.argv[1]

    try:
        # Parse URL
        pr_info = parse_github_pr_url(pr_url)

        # Fetch comments using gh CLI
        comments = fetch_github_pr_comments(
            pr_info['owner'],
            pr_info['repo'],
            pr_info['pr_number']
        )

        # Output structured JSON
        output = {
            'pr_url': pr_url,
            'platform': 'github',
            'total_comments': len(comments),
            'comments': comments
        }

        print(json.dumps(output, indent=2))

    except Exception as e:
        print(json.dumps({
            'error': str(e),
            'pr_url': pr_url
        }), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
