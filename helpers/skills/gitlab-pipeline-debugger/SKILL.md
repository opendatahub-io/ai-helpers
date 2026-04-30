---
name: gitlab-pipeline-debugger
description: Debug and monitor GitLab CI/CD pipelines for merge requests. Check pipeline status, view job logs, and troubleshoot CI failures. Use this when the user needs to investigate GitLab CI pipeline issues, check job statuses, or view specific job logs.
allowed-tools: Bash(glab:*)
---

# GitLab CI Debugger

This skill enables Claude to investigate GitLab CI pipeline failures by:

1. Checking the current pipeline status for a branch or a specific pipeline ID
2. Identifying failed jobs
3. Retrieving failed job logs
4. Analyzing error messages and suggesting fixes

## Prerequisites

- `glab` CLI installed and authenticated (`glab auth status` to verify)
- Git repository with GitLab remote configured (for automatic repo detection)

If `glab` is not installed or authenticated, provide instructions for setting it up:
- Install: https://gitlab.com/gitlab-org/cli#installation
- Authenticate: `glab auth login`

## Instructions

When the user asks to check CI status, debug pipeline failures, or view job logs, use the `glab` CLI commands below.
All commands auto-detect the GitLab project from the git remote in the current working directory.
To target a different project, add `-R <owner/group/project>` to any command.

### Handling GitLab URLs

When the user provides a full GitLab URL, parse it to extract the project path and the pipeline or job ID,
then use `-R` to target that project. **Always use the project from the URL, ignoring the local git remote.**

Before constructing any command from a URL, validate the extracted values:
- Project paths must only contain letters, digits, hyphens, underscores, dots, and forward slashes.
- Pipeline and job IDs must be purely numeric.
- Job names must only contain letters, digits, hyphens, underscores, dots, colons, slashes, and spaces.
If any value fails validation, reject it and ask the user to provide a corrected URL or ID.

- **Pipeline URL** format: `https://gitlab.com/<group>/<project>/-/pipelines/<pipeline-id>`
  - Extract: `-R <group>/<project>` and `-p <pipeline-id>`
  - Example: `https://gitlab.com/my-org/my-project/-/pipelines/123456`
    becomes `glab ci get -p 123456 -d -R my-org/my-project`

- **Job URL** format: `https://gitlab.com/<group>/<project>/-/jobs/<job-id>`
  - Extract: `-R <group>/<project>` and `<job-id>`
  - Example: `https://gitlab.com/my-org/my-project/-/jobs/789012`
    becomes `glab ci trace 789012 -R my-org/my-project`

### Commands

1. **Check Current Pipeline Status**
    - Run `glab ci get -d` to get the latest pipeline for the current branch with job details
    - This shows the pipeline metadata (ID, status, ref, user) and a table of all jobs with their status,
      duration, and failure reason

2. **Check Specific Branch**
    - Use the `-b` flag to check the pipeline for a different branch:
      `glab ci get -b <branch-name> -d`

3. **Check Specific Pipeline by ID**
    - Use the `-p` flag to inspect a pipeline directly by its ID:
      `glab ci get -p <pipeline-id> -d`

4. **View Job Logs**
    - To retrieve logs for a specific job by its numeric ID:
      `glab ci trace <job-id>`
    - To retrieve logs for a job by name within a specific pipeline:
      `glab ci trace <job-name> -p <pipeline-id>`
    - To retrieve logs for a job by name on the current branch:
      `glab ci trace <job-name>`
    - To retrieve logs for a job by name on a specific branch:
      `glab ci trace <job-name> -b <branch-name>`

5. **Find Merge Request for a Branch**
    - If the user wants MR context (title, URL, reviewers):
      `glab mr list -s <branch-name>`

6. **Troubleshoot CI Failures**
    - First, get the pipeline status to identify failed jobs (steps 1-3 above)
    - Then, retrieve the full log of the failed job (step 4)
    - Analyze the log output to identify the error and suggest fixes

## Examples

```bash
# Check CI pipeline status for the current branch
glab ci get -d
```

```bash
# Debug a failed pipeline by viewing the failed job's logs
glab ci trace 789012 -R my-org/my-project
```

## Error Handling

- If `glab` is not found, instruct the user to install it
- If `glab auth status` reports unauthenticated, instruct the user to run `glab auth login`
- If a pipeline or job is not found, show the error and suggest checking the ID or branch name
- If the repo cannot be detected, suggest using `-R <owner/group/project>` or running from within
  the correct git repository
