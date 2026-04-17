---
name: pr-jira-linker
description: Find and link Jira issues to PRs/MRs that are missing Jira references. Supports single PR/MR linking and batch audit of configured repos. Use when the user mentions "link PR to Jira", "scan PRs", "PR audit", "MR missing Jira", "link merge request", or wants to connect code changes to Jira for traceability.
user-invocable: true
---

# PR-Jira Linker

Detects PRs/MRs missing Jira references, finds or creates the matching Jira issue, and links them bidirectionally.

## Required Tools

- **GitHub** (MCP: user-github): `list_pull_requests`, `pull_request_read`, `update_pull_request`
- **GitLab** (MCP: plugin-gitlab-GitLab): `get_merge_request`, `get_merge_request_commits`, `search`, `create_workitem_note`
- **Jira** (MCP: user-mcp-atlassian): `jira_search`, `jira_add_comment`, `jira_create_issue`
- **Shell** — git commands, `curl` for GitLab API fallback

## Configuration

The skill reads repository lists and project defaults from a user-provided `config.yaml` file. A minimal example:

```yaml
defaults:
  project_key: "MYPROJECT"
  issue_type: "Task"
  security_level: "Red Hat Employee"
  priority: "Normal"
  component: "Engineering"
  team: "My Team"
  team_id: "your-team-id-here"

repos:
  gitlab:
    - project: "my-org/my-repo"
      host: "gitlab.example.com"
  github:
    - owner: "my-org"
      repo: "my-repo"
```

## Jira Key Detection

Scan for pattern `[A-Z][A-Z0-9]+-[0-9]+` in: (1) PR/MR title, (2) description, (3) branch name, (4) commit messages. If found anywhere, the PR/MR is **linked**.

## Mode 1: Single PR/MR

**Trigger**: User provides a PR/MR URL or says "link this PR to Jira".

### Step 1: Read the PR/MR

Use `pull_request_read` (GitHub) or `get_merge_request` (GitLab). If GitLab MCP is down, fall back to `curl --negotiate -u:` against the GitLab REST API. Extract title, description, branch name, author.

### Step 2: Detect Jira Reference

Scan title, description, branch, and commits for Jira key.

- **Found**: Report the key, offer to verify bidirectional link.
- **Not found**: Proceed to Step 3.

### Step 3: Find Matching Jira

Search Jira with keywords from the PR/MR title. Show matches and let user pick, or offer to create new / enter key manually / skip.

### Step 4: Link Bidirectionally

After user selects or creates a Jira issue:

**4a. Add Jira ref to PR/MR**: Use `update_pull_request` (GitHub) to append to description. For GitLab, use `create_workitem_note` to add a comment with the Jira link.

**4b. Add PR/MR link to Jira**: Use `jira_add_comment` with MR/PR URL, repo, branch, and author.

**4c. Report success**: Show both URLs and confirm what was linked.

**Never modify a PR/MR or Jira issue without showing a preview and getting user confirmation.**

## Mode 2: Batch Audit

**Trigger**: "scan PRs for missing Jira links", "PR audit", "check repos for unlinked PRs".

1. **Load repos** from config.yaml
2. **Scan** open PRs/MRs in each repo, run Jira key detection on each
3. **Report**: List missing vs. linked, offer to fix individually or fix all
4. **Fix**: Run the Single PR/MR flow for each selected item

## Creating New Jira Issues

When no matching Jira exists, the skill can create one:

1. Gather context from PR/MR content (title, description, diff)
2. Read defaults from config.yaml
3. Show defaults, ask for modifications
4. Draft issue with What/Why/What Changed sections
5. Preview and confirm
6. Create via `jira_create_issue`
7. Return to the linking step

**IMPORTANT**: Every issue MUST include `"security": {"name": "Red Hat Employee"}` and `"customfield_10001": "[TEAM_ID]"` in `additional_fields`. Never omit these fields.

## Error Handling

| Error | Action |
|-------|--------|
| GitLab MCP down | Fall back to `curl --negotiate -u:` against GitLab REST API |
| GitHub MCP not available | Skip GitHub repos, process GitLab only |
| PR/MR already linked | Report and skip (or verify bidirectional) |
| Jira search returns nothing | Offer to create new or enter key manually |
| PR/MR description update fails | Fall back to adding a comment |
| Permission denied | Inform user, suggest checking repo access |

## Examples

### Single PR Linking
```text
User: Link this PR to Jira https://github.com/my-org/my-repo/pull/42
Assistant: [Reads PR, scans for Jira key, searches Jira, links bidirectionally]
```

### Single MR Linking
```text
User: Link this MR to Jira https://gitlab.example.com/my-org/my-repo/-/merge_requests/15
Assistant: [Reads MR via API, scans for Jira key, creates or finds Jira issue, links both]
```

### Batch Audit
```text
User: Scan my repos for PRs missing Jira links
Assistant: [Loads repos from config, scans all open PRs/MRs, reports linked vs missing]
```
