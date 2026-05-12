---
name: engineer-snapshot
description: >-
  Generate an engineer activity snapshot showing active JIRA issues with
  days open, blocked work, upstream PRs awaiting review, recently merged
  PRs, and open action items from 1:1 notes. Requires a team config YAML
  file. Use when the user asks to review an engineer's status, check
  someone's workload, or prepare for a 1:1.
argument-hint: "<engineer-name> --config <path> [--jira-days N] [--github-days N]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  author: aipcc-pytorch
  version: "1.0"
  tags: reporting, jira, github, 1-on-1, engineer-management
---

# Engineer Snapshot

Generate a per-engineer activity snapshot combining JIRA issues, GitHub
PR activity, and open action items from 1:1 notes.

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `gh` CLI must be installed and authenticated (`gh auth login`)
- `JIRA_API_TOKEN` environment variable must be set with a valid API token
- `JIRA_EMAIL` environment variable must be set with your Atlassian account email
- A team config YAML file (see Config Format below)

## Config Format

Create a YAML file with your team's details (same format as
`team-weekly-report`):

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
      notes_file: "notes/engineer_one.md"  # optional
defaults:
  jira_lookback_days: 7
  github_lookback_days: 7
  stale_threshold_days: 7
```

## Implementation

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for:

- **Engineer name** (required): first positional argument
- **`--config PATH`** (required): path to team config YAML
- **`--jira-days N`** (optional): JIRA lookback for stale threshold
- **`--github-days N`** (optional): GitHub lookback for merged PRs

If the engineer name is missing, ask:

> "Which engineer should I generate a snapshot for?"

If `--config` is missing, ask:

> "Which team config file should I use? Provide the path to your YAML
> config file."

### Step 2: Load Config

Read the config file to extract the engineer's details:

- `github_username` — needed for GitHub PR queries
- `notes_file` — path to 1:1 notes (if configured)
- `team.github.repositories` — repos to search for PRs
- `defaults.github_lookback_days` — fallback for `--github-days`

### Step 3: Fetch JIRA Data

Run the JIRA fetch script to get active and blocked issues:

```bash
"${CLAUDE_SKILL_DIR}/scripts/fetch_engineer_jira.py" \
  --config <CONFIG_PATH> \
  --engineer "<ENGINEER_NAME>" \
  --days <N>
```

The script outputs JSON with `active_issues` and `blocked_issues`
arrays. Each issue includes a `days_open` field showing how many days
since creation. Capture the full JSON output.

### Step 4: Fetch Upstream PRs Open for Review

For each repository in the config, query for the engineer's open PRs
using the `gh` CLI:

```bash
gh search prs \
  --author=<GITHUB_USERNAME> \
  --repo=<REPO> \
  --state=open \
  --json number,title,url,createdAt,updatedAt \
  --limit 50
```

Run this command once per repository. Collect all results.

### Step 5: Fetch Upstream PRs Merged Recently

For each repository, query for recently merged PRs. Use
`--github-days N` if provided, otherwise use the
`defaults.github_lookback_days` value from config (fallback: 7):

```bash
gh search prs \
  --author=<GITHUB_USERNAME> \
  --repo=<REPO> \
  --merged \
  --json number,title,url,createdAt,mergedAt \
  --limit 50 \
  -- "merged:>=<CUTOFF_DATE>"
```

Where `<CUTOFF_DATE>` is today minus the lookback days in `YYYY-MM-DD`
format. Run once per repository.

### Step 6: Read 1:1 Notes

If the engineer has a `notes_file` configured in the team config, read
it using the `Read` tool. Look for open action items by searching for:

- Unchecked markdown checkboxes: `- [ ]`
- Sections titled "Action Items", "Follow-ups", or "TODO"

If no `notes_file` is configured, skip this step and note it in the
output.

### Step 7: Produce the Snapshot

Combine all collected data and produce the snapshot in the format below.
Base everything on actual data — do not assume or invent.

For each active JIRA issue, calculate the age by comparing `days_open`
to today. Flag issues that are significantly older than the team average.

## Output Format

```markdown
# Engineer Snapshot — <Engineer Name>

**Generated:** <current_date>
**Active Issues:** <count> | **Blocked:** <count> | **Open PRs:** <count>

## Active JIRA Issues

| Key | Summary | Status | Days Open | Priority |
|-----|---------|--------|-----------|----------|
[List all active issues sorted by days-open descending.
Flag issues open > 14 days with a warning indicator.]

## Blocked Issues

| Key | Summary | Days Open | Priority |
|-----|---------|-----------|----------|
[List blocked issues. If none: "No blocked issues."]

## Upstream PRs Awaiting Review

| Repo | PR | Title | Age (days) |
|------|----|-------|------------|
[List open PRs with age = days since created.
Flag PRs waiting > 7 days.]

If none: "No open PRs."

## Recently Merged PRs (Last N Days)

| Repo | PR | Title | Merged |
|------|----|-------|--------|
[List merged PRs with merge date.]

If none: "No PRs merged in this period."

## Open Action Items from 1:1 Notes

[List unchecked action items from the notes file.
If no notes file configured: "No 1:1 notes file configured."
If no open items found: "All action items are completed."]

## Suggested Talking Points

[Based on the data above, suggest 3-5 talking points for a 1:1:]

- [Accomplishments to recognize — recently closed issues or merged PRs]
- [Stale or aging work — issues open significantly longer than average]
- [Blocked work requiring escalation or support]
- [PRs waiting for review that may need attention]
- [Follow-up on open action items from previous 1:1]
```

## Error Handling

- **Engineer not found in config**: List available team members
- **Missing config file**: Ask the user for the path
- **Missing JIRA_API_TOKEN or JIRA_EMAIL**: Tell user to set env vars
- **gh not authenticated**: Tell user to run `gh auth login`
- **Script errors**: Display stderr and suggest checking credentials
- **No notes file**: Skip notes section, note in output
- **No GitHub username**: Skip PR sections, note in output

## Examples

### Basic Usage

```text
User: /engineer-snapshot "Engineer One" --config ~/team-config.yaml
Assistant: [Runs JIRA script, gh queries, reads notes, produces snapshot]
```

### Custom Lookback

```text
User: /engineer-snapshot "Engineer One" --config ~/team-config.yaml --github-days 14
Assistant: [Produces snapshot with merged PRs from last 14 days]
```

### Context Detection

```text
User: How is Engineer One doing? Can you give me a snapshot?
Assistant: I'll generate an engineer snapshot. Which config file should I use?
```
