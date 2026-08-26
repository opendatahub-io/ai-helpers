---
name: pr-jira-linker
description: Find and link Jira issues to PRs/MRs that are missing Jira references. Supports single PR/MR linking and batch audit of configured repos. Use when the user mentions "link PR to Jira", "scan PRs", "PR audit", "MR missing Jira", "link merge request", or wants to connect code changes to Jira for traceability.
user-invocable: true
allowed-tools: Read Grep Glob WebFetch Bash user-github plugin-gitlab-GitLab user-mcp-atlassian
---

# PR-Jira Linker

Detects PRs/MRs missing Jira references, finds or creates the matching Jira issue, and links them bidirectionally.

## Required Tools

- **GitHub** (MCP: user-github): `list_pull_requests`, `pull_request_read`, `update_pull_request`
- **GitLab** (MCP: plugin-gitlab-GitLab): `get_merge_request`, `get_merge_request_commits`, `search`, `create_workitem_note`
- **Jira** (MCP: user-mcp-atlassian): `jira_search`, `jira_add_comment`, `jira_create_issue`
- **Shell** — git commands, `curl` for GitLab API fallback (constrained; see safety rules below)

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

Scan for pattern `[A-Z][A-Z0-9]+-[0-9]+` in: (1) PR/MR title, (2) description, (3) branch name, (4) commit messages.
If found, mark as **candidate key detected** and verify bidirectional linkage (PR/MR references Jira key and Jira issue has PR/MR URL comment) before classifying as **linked**.

## Mode 1: Single PR/MR

**Trigger**: User provides a PR/MR URL or says "link this PR to Jira".

### Step 1: Read the PR/MR

Use `pull_request_read` (GitHub) or `get_merge_request` (GitLab). If GitLab MCP is down, fall back to `curl --negotiate -u:` against the GitLab REST API under the following **mandatory safety constraints**:

1. **Host allowlist**: Only issue requests to hostnames explicitly listed in `config.yaml` under `repos.gitlab[].host`. Reject any target not in the allowlist.
2. **No raw IPs**: Reject URLs containing raw IP addresses (IPv4 or IPv6). Resolve hostnames and reject any that resolve to private/reserved ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16, ::1, fc00::/7, fe80::/10) to prevent SSRF.
3. **URL canonicalization**: Parse the URL, verify scheme is `https://`, and reconstruct from validated components. Do not pass user-supplied URLs directly to shell commands.
4. **Safe argument passing**: Pass URL, host, and path as separate, safely shell-quoted arguments. Never string-concatenate untrusted input into commands. Pass credentials via environment variables (e.g., `GITLAB_TOKEN`), not interpolated into command strings.
5. **Resource limits**: Always use `--max-time 30 --max-redirs 3` to enforce timeouts and limit redirects.
6. **Protocol restriction**: Use `--proto '=https'` to prevent protocol downgrade or scheme switching.

Extract title, description, branch name, author.

### Step 2: Detect Jira Reference

Scan title, description, branch, and commits for Jira key.

- **Found**: Report candidate key and verify bidirectional link status before deciding skip/fix.
- **Not found**: Proceed to Step 3.

### Step 3: Find Matching Jira

Search Jira with **escaped/sanitized** keywords from the PR/MR title (treat user text as data, not query syntax). Strip or escape JQL/Lucene operators (`+ - && || ! ( ) { } [ ] ^ " ~ * ? : \ /`) before constructing the query. If sanitized tokens are empty, fall back to prompting the user for manual input. Show matches and let user pick, or offer to create new / enter key manually / skip.

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
3. **Report**: List missing vs. linked (verified bidirectionally), offer to fix individually or fix all
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
| GitLab MCP down | Fall back to `curl --negotiate -u:` **only** for hosts allowlisted in `config.yaml`; reject non-allowlisted targets and raw IPs; enforce `--max-time 30 --max-redirs 3 --proto '=https'`; pass credentials via env vars |
| GitHub MCP not available | Skip GitHub repos, process GitLab only |
| PR/MR already linked | Verify bidirectional linkage, report and skip if confirmed |
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
