---
name: pipeline-debugger
description: Debug and monitor GitLab CI/CD pipelines for merge requests. Check pipeline status, view job logs, and troubleshoot CI failures. Use this when the user needs to investigate GitLab CI pipeline issues, check job statuses, or view specific job logs.
allowed-tools: Bash, Read
---

# GitLab CI Debugger

This skill helps debug and monitor GitLab CI/CD pipelines associated with merge requests. It can check pipeline status,
display job information grouped by stage, and retrieve logs for specific jobs.

This skill enables Claude to investigate GitLab CI pipeline failures by:

1. Checking the current branch's MR pipeline status
2. Identifying failed jobs
3. Retrieving failed job logs
4. Analyzing error messages and suggesting fixes

## Prerequisites

- Git repository with GitLab remote configured
- GitLab authentication via GITLAB_TOKEN env var or .netrc file

The script will fail if it detects any missing configuration. Interpret the error message and provide instructions
for setting up the required configuration.

## Instructions

When the user asks to check CI status, debug pipeline failures, or view job logs:

1. **Check Current Pipeline Status**
    - Use the `./scripts/check_mr_pipeline.py` script without arguments to check the current branch's MR pipeline status
    - The script will display all jobs grouped by stage with status indicators

2. **Check Specific Branch**
    - If the user asks to check on the pipeline status for a different branch than the current one, use the `-b` or
      `--branch` option to specify that branch.
        - Example: `./scripts/check_mr_pipeline.py -b feature-branch`

3. **View Job Logs**
    - Use the `-j` or `--job` option to retrieve and display logs for a specific job
    - Example: `./scripts/check_mr_pipeline.py -j "test-job-name"`
    - The script will show the job's metadata and full log output

4. **Troubleshoot CI Failures**
    - If the user asks to troubleshoot a CI failure, use the full log output of a job to identify the error and suggest
      fixes.

## Troubleshooting

- **No open merge request found**: Ensure there's an open MR for the branch
- **Authentication errors when running the script**: Instruct user to set up GITLAB_TOKEN or .netrc file
- **Job not found**: Use the script without `-j` option first to see available job names
