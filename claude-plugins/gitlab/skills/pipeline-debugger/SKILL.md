---
name: pipeline-debugger
description: Debug and monitor GitLab CI/CD pipelines for merge requests. Check pipeline status, view job logs, and troubleshoot CI failures. Use this when the user needs to investigate GitLab CI pipeline issues, check job statuses, or view specific job logs.
allowed-tools: Bash, Read
---

# GitLab CI Debugger

This skill enables Claude to investigate GitLab CI pipeline failures by:

1. Checking the current pipeline status for a branch, merge request, or a specific pipeline ID
2. Identifying failed jobs
3. Retrieving failed job logs
4. Analyzing error messages and suggesting fixes

## Prerequisites

- Git repository with GitLab remote configured
- GitLab authentication via GITLAB_TOKEN env var or .netrc file

The script will fail if it detects any missing configuration. Interpret the error message and provide instructions
for setting up the required configuration.

## Instructions

**IMPORTANT**: Always run the script from the user's current working directory (where Claude was launched), NOT from the
skill directory. The script needs access to the git repository context. Use the base directory (`<base_path>`) for this
skill to execute the script with an absolute path.

When the user asks to check CI status, debug pipeline failures, or view job logs:

1. **Check Current Pipeline Status**
    - Run `<base_path>/scripts/check_pipeline.py` without arguments to check the current branch's pipeline status
    - The script will display all jobs grouped by stage with status indicators

2. **Check Specific Branch**
    - If the user asks to check on the pipeline status for a different branch than the current one, use the `-b` or
      `--branch` option to specify that branch.
        - Example: `<base_path>/scripts/check_pipeline.py -b feature-branch`

3. **Check Specific Pipeline by ID**
    - If the user provides a pipeline ID directly, use the `-p` or `--pipeline-id` option to inspect that pipeline
    - This skips the merge request lookup and directly inspects the specified pipeline
    - Example: `<base_path>/scripts/check_pipeline.py -p 12519874995`
    - Note: `--pipeline-id` and `--branch` are mutually exclusive

4. **View Job Logs**
    - Use the `-j` or `--job` option to retrieve and display logs for a specific job
    - Example: `<base_path>/scripts/check_pipeline.py -j "test-job-name"`
    - Can be combined with any of the above options (branch, pipeline ID, or current branch)
    - The script will show the job's metadata and full log output

5. **Troubleshoot CI Failures**
    - If the user asks to troubleshoot a CI failure, use the full log output of a job to identify the error and suggest
      fixes.
