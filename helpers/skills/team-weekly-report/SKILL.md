---
name: team-weekly-report
description: >-
  Generate a weekly team status report combining JIRA and GitHub data.
  Fetches closed, open, stale, and blocked issues plus PR activity for
  each team member. Requires a team config YAML file with JIRA project,
  GitHub repos, and team member mappings. Use when the user asks for a
  weekly report, team status, or team update.
argument-hint: "--config <path-to-team-config.yaml> [--days N]"
allowed-tools: Bash
user-invocable: true
metadata:
  author: aipcc-pytorch
  version: "1.0"
  tags: reporting, jira, github, team-management, weekly-report
---

# Team Weekly Report

Generate a comprehensive weekly status report for an engineering team by
combining JIRA issue data and GitHub PR activity.

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `gh` CLI must be installed and authenticated (`gh auth login`)
- `JIRA_API_TOKEN` environment variable must be set with a valid API token
- `JIRA_EMAIL` environment variable must be set with your Atlassian account email
- A team config YAML file (see Config Format below)

## Config Format

Create a YAML file with your team's details:

```yaml
team:
  name: "My Team"
  jira:
    url: "https://mycompany.atlassian.net"
    project: "PROJ"
    component: "MyComponent"  # optional
  github:
    repositories:
      - "org/repo1"
      - "org/repo2"
  members:
    - name: "Engineer One"
      jira_username: "712020:account-id-here"
      github_username: "eng1"
    - name: "Engineer Two"
      jira_username: "712020:account-id-here"
      github_username: "eng2"
defaults:
  jira_lookback_days: 7
  github_lookback_days: 7
  stale_threshold_days: 7
```

**Finding JIRA account IDs:** In Jira Cloud, go to a user's profile page.
The account ID is the long string in the URL after `/people/`.

## Implementation

### Step 1: Determine Config Path

Parse `$ARGUMENTS` for the `--config` flag and optional `--days` flag.

If no `--config` is provided, ask the user:

> "Which team config file should I use? Provide the path to your YAML
> config file (e.g., `~/team-config.yaml`)."

Validate the config file exists before proceeding.

### Step 2: Fetch JIRA Data

Run the JIRA fetch script to collect closed, open, stale, and blocked
issues for every team member:

```bash
"${CLAUDE_SKILL_DIR}/scripts/fetch_team_jira.py" --config <CONFIG_PATH> --days <N>
```

The script outputs JSON to stdout with a `members` array. Each member
entry contains `closed_issues`, `open_issues`, `stale_issues`, and
`blocked_issues` arrays. Capture the full JSON output for analysis.

If the script fails, display the error and stop.

### Step 3: Fetch GitHub Data

Run the GitHub fetch script to collect open and merged PRs for every
team member across the configured repositories:

```bash
"${CLAUDE_SKILL_DIR}/scripts/fetch_team_github.py" --config <CONFIG_PATH> --days <N>
```

The script outputs JSON to stdout with a `members` array. Each member
entry contains `open_prs` and `merged_prs` arrays. Capture the full
JSON output.

If the script fails, display the error but continue with JIRA data only.

### Step 4: Produce the Report

Combine the JIRA and GitHub JSON outputs and produce the report in the
format below. Base everything on actual data — do not assume or invent.

For each team member, correlate their JIRA activity with their GitHub
activity to build a complete picture.

## Output Format

```markdown
# Weekly Status Report — <Team Name>

**Period:** <start_date> to <end_date>
**Generated:** <current_date>

## Executive Summary

[2-3 sentences: major accomplishments, key metrics, overall team health.
Mention any critical blockers or risks.]

## Team Velocity

- Issues closed this week: [count]
- Issues currently open: [count]
- PRs merged: [count]
- PRs open for review: [count]
- Blocked issues: [count]
- Stale issues (no update in N+ days): [count]

## Individual Updates

[For each team member:]

### <Engineer Name>

**Completed:** [Issues closed this week — list key, summary]
**In Progress:** [Open issues — list key, summary, status]
**PRs:** [Open and merged PRs with repo and title]
**Blockers:** [Any blocked issues, or "None"]

## Open PRs

| Author | Repo | PR | Title | Age |
|--------|------|----|-------|-----|
[List all open PRs from team members. Age = days since created.]

## PRs Merged This Week

| Author | Repo | PR | Title | Merged |
|--------|------|----|-------|--------|
[List all PRs merged in the lookback window.]

## Stale Issues (No Updates in N+ Days)

[Group by engineer. These are potential risks — work that may be stuck.]

| Engineer | Key | Summary | Status | Last Updated |
|----------|-----|---------|--------|--------------|

## Blockers & Risks

[List all blocked issues with key, summary, and assignee.
Flag stale issues as additional risk signals.
Note any team members with no activity.]
```

## Error Handling

- **Missing config file**: Ask the user for the path
- **Missing JIRA_API_TOKEN or JIRA_EMAIL**: Tell user to set env vars
- **gh not authenticated**: Tell user to run `gh auth login`
- **Script errors**: Display stderr output and suggest checking credentials
- **No data for a member**: Note it in the report rather than failing

## Examples

### Basic Usage

```text
User: /team-weekly-report --config ~/team-config.yaml
Assistant: [Runs both scripts, produces weekly report]
```

### Custom Lookback Window

```text
User: /team-weekly-report --config ~/team-config.yaml --days 14
Assistant: [Produces report covering last 14 days]
```

### No Arguments

```text
User: /team-weekly-report
Assistant: Which team config file should I use? Provide the path...
```
