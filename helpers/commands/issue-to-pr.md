---
description: Analyze a GitHub or GitLab issue and drive toward a PR or ask for clarification. Use when the user provides an issue URL or pasted issue details.
argument-hint: [issue-url] or pasted issue title/body
---

## Name
odh-ai-helpers:issue-to-pr

## Synopsis
```
/issue-to-pr [issue-url]
```

## Description
Analyze a GitHub or GitLab issue and drive toward a PR or ask for clarification. Use this command when the user provides a **GitHub or GitLab issue URL** (or pastes issue title and body). Your goal is to analyze the issue and either drive toward a PR or ask for clarification.

## Implementation

### Input

The user will provide one of:
- A GitHub issue URL (e.g. `https://github.com/owner/repo/issues/123`)
- A GitLab issue URL (e.g. `https://gitlab.com/owner/repo/-/issues/456`)
- Pasted issue details (title, body)

Treat that as **the issue** to analyze.

### 1. Resolve issue content

- If a URL was given: fetch the issue page and **read the comments** as well as the title and body. Use the full issue URL (e.g. `https://github.com/owner/repo/issues/123`); if the page is large, fetch it and parse or fetch comment threads so you see maintainer suggestions, alternative approaches, and convention preferences. If fetch fails or comments are unavailable, ask the user to paste any relevant comments.
- If the user pasted details: use the provided title and body, and ask whether there are important comments on the issue they can paste.

### 2. Analyze clarity and comments

- Determine whether the issue has **clear requirements** (acceptance criteria, scope, and enough detail to implement).
- **Use comments to inform the solution**: Prefer approaches suggested or endorsed by maintainers (e.g. "we should enforce X" or "follow the same convention as Y"). If a comment contradicts a naive fix from the issue body, follow the comment. Mention in your response when comments changed or guided your approach.

### 3a. If requirements are clear

1. **Create branch**: `<issue_description>` (e.g. `add_xyz`).
2. **Implement** the fix or feature described in the issue, following any approach or convention indicated in the issue comments.
3. **Run tests** (e.g. repo test commands).
4. **Produce a draft PR** that:
   - Uses the repo's PR template if one exists (e.g. in `.github/PULL_REQUEST_TEMPLATE.md` or `.github/pull_request_template.md`).
   - Includes a short summary, list of changes, and test plan.

Do not actually open the PR via API unless the user asks; output the branch name, commit message suggestion, and PR title/body (template) for them to use.

### 3b. If requirements are unclear

Reply with a **clarification request** on the issue. For example:

- What exactly should be implemented or fixed?
- What are the acceptance criteria or expected behavior?
- Any constraints (versions, platforms, breaking changes)?
- Links or examples if relevant.

Ask the user to add these details so you can proceed with the "requirements clear" path.

### References

- Prefer creating branches with: `<issue_description>`.
- If you are in agent mode, update the code and add/run tests if necessary. Do not commit the code yourself.
- If you are in ask mode, provide the changes needed to fix the issue and explain your reasoning.
