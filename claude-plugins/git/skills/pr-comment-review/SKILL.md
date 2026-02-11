---
name: pr-comment-review
description: Analyze Pull Request comments and generate structured action plans with severity rankings and response suggestions
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
---

# PR Comment Review & Action Plan Generator

This skill analyzes all comments from a Pull Request and generates a comprehensive action plan report with severity rankings, validity assessments, and suggested responses.

## Instructions

When this skill is invoked, follow these steps to analyze PR comments and generate an action plan:

### 1. Fetch PR Comments

**Command:**
```bash
./claude-plugins/git/skills/pr-comment-review/scripts/analyze_pr_comments.py {{ worktree.pull_request_url }}
```

This script will:
- Fetch all review comments and general comments from the PR using `gh` CLI
- Support GitHub PRs (authenticated via `gh auth login`)
- Output structured JSON with comment details

**Expected Output:**
```json
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "platform": "github",
  "total_comments": 5,
  "comments": [
    {
      "id": 12345,
      "type": "review",
      "author": "reviewer",
      "body": "Comment text...",
      "path": "src/file.py",
      "line": 42,
      "created_at": "2024-01-01T12:00:00Z",
      "url": "https://github.com/..."
    }
  ]
}
```

### 2. Read the Template

Read the template file to understand the structure and guidelines:
```bash
./claude-plugins/git/skills/pr-comment-review/template.md
```

The template contains comprehensive documentation including:
- **Severity Classification Guide**: Criteria for High/Medium/Low severity
- **Reasonableness Check Framework**: How to evaluate comment validity
- **Alternative Approaches Framework**: How to present solution options
- **Response Tone Guidelines**: How to craft professional responses
- **Issue and Response Templates**: Exact formatting to use

**Important**: Follow ALL guidance provided in the template file. It is self-documenting and comprehensive.

### 3. Analyze and Categorize Comments

Using the Severity Classification Guide from the template:
1. Review each comment from the fetched data
2. Categorize as High, Medium, or Low severity
3. Apply the Reasonableness Check Framework to assess validity
4. Determine appropriate actions using the template's guidance
5. For complex issues, provide alternative approaches per the template's framework

### 4. Generate the Report

**File Location:** `temp/pr_code_review###.md`

**Naming Convention:**
- Find the highest existing iteration number in `temp/pr_code_review*.md`
- Increment by 1 for this report
- If no previous reports exist, start with `temp/pr_code_review001.md`

**Generation Process:**
1. The template file (already read in step 2) contains all placeholders and instructions
2. Replace all `{PLACEHOLDER}` values with actual content from your analysis
3. Format issues using the Issue Template format (defined in the template)
4. Format responses using the Response Template format (defined in the template)
5. Remove the template sections at the bottom (marked with HTML comments)
6. Write the completed report to `temp/pr_code_review###.md`

**Note**: All formatting instructions, placeholder definitions, and guidelines are in the template file itself. Refer to it for complete details.

### 5. Output Confirmation

After creating the report, inform the user:
```
✓ PR Comment Analysis Complete

Report saved to: temp/pr_code_review###.md

Summary:
- Total comments analyzed: X
- High severity: Y issues
- Medium severity: Z issues
- Low severity: W issues

Next: Review the action plan and address issues by priority.
```

## Prerequisites

**Required Tools:**
- `gh` CLI (GitHub CLI) must be installed and authenticated
  - Install: https://cli.github.com/
  - Authenticate: `gh auth login`

**Context Variables:**
- `{{ worktree.pull_request_url }}`: The URL of the PR to analyze

If the PR URL is not available in the worktree context, ask the user to provide it.

## Usage Examples

### Example 1: Analyze Current PR
```
User: /pr-comment-review https://github.com/owner/repo/pull/123
```

The skill will analyze the specified PR URL instead of the worktree context.

### Example 2: Analyze Specific PR
```
User: /pr-comment-review
```

The skill will use `{{ worktree.pull_request_url }}` from the current worktree context.

### Example 3: Review Multiple Iterations
```
User: /pr-comment-review

[After addressing some issues and receiving new comments]

User: /pr-comment-review
```

The skill will create `temp/pr_code_review002.md` with updated analysis.

## Error Handling

**Missing PR URL:**
```
Error: No PR URL provided and worktree.pull_request_url is not set.

Please either:
1. Provide a PR URL: /pr-comment-review <url>
2. Set the PR URL in your worktree context
```

**Authentication Issues:**
```
Error: gh CLI not found or not authenticated.

Please:
1. Install gh CLI: https://cli.github.com/
2. Authenticate: gh auth login
```

**Invalid PR URL:**
```
Error: Unsupported or invalid PR URL format.

Supported format:
- GitHub: https://github.com/owner/repo/pull/123
```

**No Comments Found:**
```
No active comments found on this PR.

This could mean:
1. The PR has no comments yet
2. All comments have been resolved
3. The gh CLI is not authenticated (run: gh auth login)

Report saved with 0 issues: temp/pr_code_review###.md
```

## Integration Notes

**Workflow Integration:**
1. After receiving PR review comments, invoke this skill
2. Review the generated action plan
3. Address issues by priority (High → Medium → Low)
4. Use the suggested responses to reply to reviewers
5. Re-run the skill after addressing issues to track progress

**Best Practices:**
- Run this skill immediately after receiving PR reviews
- Keep iterations to track how issues are resolved over time
- Use the alternative approaches to make informed decisions
- Customize the suggested responses to match your communication style

**Related Skills:**
- Can be used alongside Git skills for implementing fixes
- Integrates with issue tracking for linking to tickets
- Complements CI/CD debugging for build-related comments
