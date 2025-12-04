#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
# ]
# ///
"""
Check CI pipeline status for the merge request associated with a git branch.

Authentication (checked in order):
  1. GITLAB_TOKEN environment variable
  2. NETRC environment variable (path to .netrc file)
  3. ~/.netrc file (default location)

Environment variables:
  GITLAB_TOKEN - GitLab personal access token (preferred)
  NETRC - Path to .netrc file (default: ~/.netrc)
  GITLAB_PROJECT_PATH - Override project path (by default "origin" from .git/config)
  GITLAB_DOMAIN - Override default GitLab domain ("gitlab.com")
"""

import argparse
import netrc
import os
import re
import subprocess
import sys
from collections import defaultdict
from typing import Any

import gitlab
from gitlab.v4.objects import Project, ProjectMergeRequest, ProjectPipeline

STATUS_EMOJIS = {
    "success": "✓",
    "failed": "✗",
    "running": "▶",
    "pending": "○",
    "canceled": "⊗",
    "skipped": "⊘",
    "manual": "⚙",
    "created": "◯",
}


def display_pipeline_status(pipeline: ProjectPipeline) -> None:
    """Display the status of all jobs in a pipeline."""
    project = pipeline.manager.gitlab.projects.get(pipeline.project_id)
    jobs = project.pipelines.get(pipeline.id).jobs.list(get_all=True)
    if not jobs:
        print("No jobs found in this pipeline.")
        return

    # Group jobs by stage; sort by when they started so stages display in order
    jobs_by_stage: dict[str, list[Any]] = defaultdict(list)
    max_job_name_len = 0
    for job in sorted(jobs, key=lambda j: j.started_at):
        jobs_by_stage[job.stage].append(job)
        max_job_name_len = max(max_job_name_len, len(job.name))

    # Display jobs grouped by stage (retain order from above)
    for stage in jobs_by_stage.keys():
        print(stage)
        for job in sorted(jobs_by_stage[stage], key=lambda j: j.name):
            status = job.status
            emoji = STATUS_EMOJIS.get(status, "?")
            print(f"  {job.name:<{max_job_name_len}}   {emoji} {status}")


def view_job_log(pipeline: ProjectPipeline, job_name: str) -> None:
    """Download and print the log for a specific job (by name)."""
    project = pipeline.manager.gitlab.projects.get(pipeline.project_id)
    jobs = project.pipelines.get(pipeline.id).jobs.list(get_all=True)

    matching_jobs = [job for job in jobs if job.name == job_name]
    if not matching_jobs:
        print(f"ERROR: Job '{job_name}' not found.", file=sys.stderr)
        print("\nAvailable jobs:", file=sys.stderr)
        for job in sorted(jobs, key=lambda j: j.name):
            print(f"  {job.name}", file=sys.stderr)
        sys.exit(1)

    job = matching_jobs[0]
    # Get the full job object (list() returns partial objects without trace())
    full_job = project.jobs.get(job.id)

    print(f"\n{'=' * 80}")
    print(f"Job: {full_job.name}")
    print(f"Status: {full_job.status}")
    print(f"Stage: {full_job.stage}")
    print(f"Web URL: {full_job.web_url}")
    print(f"{'=' * 80}\n")

    log = full_job.trace().decode("utf-8")
    print(log)


def find_mr_for_branch(
    project: Project, branch_name: str
) -> ProjectMergeRequest | None:
    """Find an open merge request associated with a given branch."""
    mrs = project.mergerequests.list(
        source_branch=branch_name, state="opened", get_all=True
    )
    if not mrs:
        return None
    # Return the first (most recent) MR
    return mrs[0]


def get_latest_pipeline(mr: ProjectMergeRequest) -> ProjectPipeline | None:
    """Get the latest pipeline for a merge request."""
    pipelines = mr.pipelines.list(get_all=True)
    if not pipelines:
        return None
    # Pipelines are returned in newest to oldest
    return pipelines[0]


def get_current_branch() -> str:
    """Get the current git branch name."""
    result = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    )
    return result.strip()


def get_gitlab_token(domain: str) -> str:
    """Get GitLab authentication token from environment variable or netrc file."""
    if token := os.environ.get("GITLAB_TOKEN"):
        return token

    # Check for NETRC environment variable, otherwise use default ~/.netrc
    netrc_file_path = os.environ.get("NETRC") or "~/.netrc"
    try:
        n = netrc.netrc(netrc_file_path)
        authenticator = n.authenticators(domain)
        if authenticator:
            token = authenticator[-1]
        if token:
            return token
        else:
            raise ValueError(
                f"ERROR: No applicable token found for {domain} in {netrc_file_path}"
            )
    except FileNotFoundError:
        pass
    print(
        f"ERROR: No GitLab token found; set GITLAB_TOKEN environment variable or "
        f"add {domain} credentials to a .netrc file",
        file=sys.stderr,
    )
    sys.exit(1)


def get_gitlab_info() -> tuple[str, str]:
    """Get GitLab domain and project path from environment or git remote origin."""
    if proj_path := os.environ.get("GITLAB_PROJECT_PATH"):
        # If only project path is provided, assume gitlab.com as default domain
        gitlab_domain = os.environ.get("GITLAB_DOMAIN", "gitlab.com")
        return gitlab_domain, proj_path

    try:
        remote_url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Failed to get git remote origin: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse HTTPS format: https://[gitlab-domain]/group/subgroup/project.git
    if match := re.match(r"https://([^/]+)/(.+?)(?:\.git)?$", remote_url):
        gitlab_domain = match.group(1)
        project_path = match.group(2)
        return gitlab_domain, project_path

    # Parse SSH format: git@[gitlab-domain]:group/subgroup/project.git
    if match := re.match(r"git@([^:]+):(.+?)(?:\.git)?$", remote_url):
        gitlab_domain = match.group(1)
        project_path = match.group(2)
        return gitlab_domain, project_path

    print(
        f"ERROR: Could not parse GitLab domain and project path from remote URL: {remote_url}",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-b",
        "--branch",
        help="Git branch name (default: current branch)",
        default=None,
    )
    parser.add_argument(
        "-j",
        "--job",
        help="Download and print the log for the specified job name",
        default=None,
    )
    args = parser.parse_args()

    branch_name = args.branch if args.branch else get_current_branch()
    if branch_name == "main":
        print(
            "WARNING: You are on the 'main' branch; this will display the latest CI run on main",
            file=sys.stderr,
        )

    gitlab_domain, project_path = get_gitlab_info()
    gitlab_url = f"https://{gitlab_domain}"
    token = get_gitlab_token(gitlab_domain)
    gl = gitlab.Gitlab(url=gitlab_url, private_token=token)
    gl.auth()

    project = gl.projects.get(project_path)

    mr = find_mr_for_branch(project, branch_name)
    if not mr:
        print(
            f"ERROR: No open merge request found for branch '{branch_name}'",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Found MR !{mr.iid}: {mr.title}")
    print(f"MR URL: {mr.web_url}")

    pipeline = get_latest_pipeline(mr)
    if not pipeline:
        print(f"ERROR: No pipeline found for merge request !{mr.iid}", file=sys.stderr)
        sys.exit(1)

    if args.job:
        view_job_log(pipeline, args.job)
    else:
        print(f"{'=' * 80}")
        display_pipeline_status(pipeline)


if __name__ == "__main__":
    main()
