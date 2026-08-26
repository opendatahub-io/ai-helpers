---
name: github-actions-debugger
description: Debug and monitor GitHub Actions workflow runs. Check run status, view failed job logs, and troubleshoot CI failures. Use this when the user needs to investigate GitHub Actions failures, inspect job output, or identify the root cause of a broken workflow run.
allowed-tools: Bash(gh:*)
---

# GitHub Actions Debugger

This skill enables Claude to investigate GitHub Actions failures by:

1. Listing recent workflow runs and their status
2. Identifying failed jobs within a run
3. Retrieving failed job logs
4. Analyzing error messages and suggesting next debugging steps

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status` to verify)
- Git repository with a GitHub remote configured (for automatic repo detection)

If `gh` is not installed, ask the user to follow installation instructions at https://cli.github.com/

If `gh` is not authenticated, ask the user to run `gh auth login`.

## Instructions

When the user asks to check CI status, debug workflow failures, or view job logs, use the `gh` CLI commands below.
All commands auto-detect the GitHub repository from the git remote in the current working directory.
To target a different repository, add `-R <owner>/<repo>` to any command.

### Handling GitHub Actions URLs

When the user provides a full GitHub Actions URL, parse it to extract the repository and run or job ID,
then use `-R` to target that repository. **Always use the repository from the URL, ignoring the local git remote.**

Before constructing any command from a URL, validate the extracted values:
- Owner names must only contain letters, digits, and hyphens.
- Repository names must only contain letters, digits, hyphens, underscores, and dots.
- Run IDs and job IDs must be purely numeric.
- Workflow file names must only contain letters, digits, hyphens, underscores, and dots.
If any extracted value fails its rule, reject it and ask the user to provide a corrected URL or ID.

- **Run URL** format: `https://github.com/<owner>/<repo>/actions/runs/<run-id>`
  - Extract: `-R <owner>/<repo>` and `<run-id>`
  - Example: `https://github.com/my-org/my-project/actions/runs/123456789`
    becomes `gh run view 123456789 -R my-org/my-project`

- **Workflow URL** format: `https://github.com/<owner>/<repo>/actions/workflows/<workflow-file>`
  - Extract: `-R <owner>/<repo>` and `--workflow <workflow-file>`
  - Example: `https://github.com/my-org/my-project/actions/workflows/ci.yaml`
    becomes `gh run list --workflow ci.yaml -R my-org/my-project`

### Commands

1. **List Recent Workflow Runs**
    - Run `gh run list --limit 10` to show the latest runs with their status, workflow name, and run ID
    - Add `--status failure` to filter for only failed runs:
      `gh run list --status failure --limit 10`

2. **Filter by Workflow File**
    - Use `--workflow` to scope results to a specific workflow:
      `gh run list --workflow ci.yaml --limit 10`

3. **View a Specific Run**
    - Use `gh run view <run-id>` to see the run summary including all jobs and their status:
      `gh run view <run-id>`
    - Add `--log-failed` to immediately stream the logs of all failed jobs:
      `gh run view <run-id> --log-failed`

4. **View Full Logs for a Run**
    - To retrieve complete logs for every job in a run:
      `gh run view <run-id> --log`
    - Pipe through `grep` to isolate errors:
      `gh run view <run-id> --log-failed 2>&1 | grep -i "error\|fail\|fatal" | head -50`

5. **Watch a Running Workflow**
    - To follow a currently active run in real time:
      `gh run watch <run-id>`

6. **Re-run Failed Jobs**
    - If the user wants to retry only the failed jobs without re-running passing ones:
      `gh run rerun <run-id> --failed`

7. **Troubleshoot CI Failures**
    - First, list recent failed runs to identify the run ID (step 1)
    - Then, view the run to see which jobs failed (step 3)
    - Then, retrieve the failed job logs (step 3 with `--log-failed`)
    - Analyze the log output to identify the root cause and suggest fixes

## Examples

```bash
# List the 10 most recent runs across all workflows
gh run list --limit 10
```

```bash
# Show only failed runs for a specific workflow
gh run list --workflow ci.yaml --status failure --limit 10
```

```bash
# View run summary and failed job logs for run ID 123456789
gh run view 123456789 --log-failed
```

```bash
# Grep failed logs for actionable errors
gh run view 123456789 --log-failed 2>&1 | grep -i "error\|fail\|fatal" | head -50
```

```bash
# Re-run only the failed jobs
gh run rerun 123456789 --failed
```

## Error Handling

- If a run ID is not found, show the error and suggest running `gh run list` to find the correct ID
- If the repository cannot be detected, suggest using `-R <owner>/<repo>` or running from within the correct git repository
- If logs are unavailable (e.g., run too old or log retention expired), inform the user and suggest checking the GitHub Actions UI directly
