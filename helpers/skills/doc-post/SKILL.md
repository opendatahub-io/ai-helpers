---
name: doc-post
description: >
  Post validation and review findings as comments on a GitHub PR or
  GitLab MR. Reads workspace findings files and formats them as
  inline or summary comments.
argument-hint: "<PR-URL> [--validation] [--review] [--all]"
model: claude-haiku-3-5
effort: low
---

# doc-post

Post validation and review findings as comments on a PR/MR.

## Parse arguments

`$ARGUMENTS` contains:
1. **PR URL**: GitHub or GitLab PR/MR URL (required)
2. **Flags** (optional):
   - `--validation`: post validation findings only
   - `--review`: post review findings only
   - `--all` (default): post both validation and review findings

## Step 1: Detect platform

From the PR URL, determine the platform:
- `github.com` → GitHub (use `gh` CLI)
- Other → GitLab (use GitLab API)

## Step 2: Load findings

Based on flags, read the relevant findings files:

- **Validation**: `workspace/validation-findings.json`
- **Review**: `workspace/review-findings.json`

If a requested file doesn't exist, warn and skip it.

## Step 3: Format comments

### Summary comment

Create a summary comment with an overview table:

```markdown
## Documentation Review Results

| Category | High | Medium | Low | Total |
|----------|------|--------|-----|-------|
| Validation | 0 | 3 | 5 | 8 |
| Review | 1 | 2 | 3 | 6 |
| **Total** | **1** | **5** | **8** | **14** |

**Review confidence**: 0.78

### High-severity findings

1. **[ref_model-serving-params.adoc:42]** Technical inaccuracy: The documented API field 'replicas' should be 'minReplicas'
   - **Suggestion**: Change 'replicas' to 'minReplicas' per the CRD type definition

### Medium-severity findings

1. **[con_model-serving.adoc:15]** Vale: Use 'Red Hat OpenShift AI' instead of 'RHOAI' on first reference
```

### Inline comments (GitHub only)

For findings that reference specific files and lines in the PR's changed files:

1. Get the list of changed files: `gh pr view <URL> --json files`
2. For each finding that references a changed file, post an inline review comment
3. For findings in files not in the PR diff, include them in the summary comment

## Step 4: Post comments

### GitHub

```bash
# Post summary comment
gh pr comment <PR-URL> --body "<summary>"

# Post inline review (if applicable)
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  --method POST \
  --field body="Documentation review complete" \
  --field event="COMMENT" \
  --field comments="[...]"
```

### GitLab

Use the GitLab API to post merge request notes.

## Step 5: Report

Report to caller:
- Number of comments posted
- Summary of findings posted
- Any findings that could not be posted (e.g., file not in PR diff)

## Output

Comments posted on the PR/MR. No workspace file produced.

## Stop conditions

- **Halt**: PR URL not provided or invalid
- **Halt**: No findings files exist
- **Warn**: `gh` CLI not available (cannot post to GitHub)
- **Continue**: Some inline comments fail to post (include in summary instead)
