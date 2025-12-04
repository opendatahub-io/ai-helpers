---
description: Generate AIPCC Commits style commit messages or summarize existing commits
argument-hint: [N]
---

## Name
git:aipcc-commit-suggest

## Synopsis
```
/git:aipcc-commit-suggest       # Analyze staged changes
/git:aipcc-commit-suggest [N]     # Analyze last N commits (1-100)
```

## Description
AI-powered command that analyzes code changes and generates commit messages following the project's AIPCC format requirements.

**Modes:**
- **Mode 1 (no argument)** – Analyze staged changes (`git add` required)
- **Mode 2 (with N)** – Analyze last N commits to rewrite (N=1) or summarize for squash (N≥2)

**Use cases:**
- Create AIPCC-formatted commit messages
- Improve or rewrite existing commits to meet project standards
- Generate squash messages for MR merges

**Difference from `/git:summary`** – That command is read-only, while `git:aipcc-commit-suggest` generates actionable commit message suggestions for user review and manual use.

## Implementation

The command operates in two modes based on input:

**Mode 1 (no argument):**
1. Collect staged changes via `git diff --cached`
2. Analyze file paths and code content to determine appropriate AIPCC ticket reference
3. Generate 3 AIPCC-formatted commit message suggestions (Recommended, Standard, Minimal)
4. Display formatted suggestions and prompt user for selection
   - Ask: "Which suggestion would you like to use? (1/2/3 or skip)"
   - Support responses: `1`, `use option 2`, `commit with option 3`, `skip`
   - Execute `git commit -s` with selected message if user requests (includes sign-off)

**Mode 2 (with N):**
1. Retrieve last N commits using `git log`
2. Parse commit messages and analyze changes to maintain AIPCC format consistency
3. For **N=1**: Suggest improved rewrite following AIPCC format
   For **N≥2**: Merge commits into unified AIPCC-formatted squash message
4. Generate 3 AIPCC-formatted commit message suggestions (Recommended, Standard, Minimal)
5. Display formatted suggestions and prompt user for selection
   - Ask: "Which suggestion would you like to use? (1/2/3 or skip)"
   - Support responses: `1`, `use option 2`, `amend with option 3`, `skip`
   - Execute `git commit --amend -s` (N=1) or squash operation (N≥2) if user requests

## Examples

```bash
# Generate message for staged files
git add src/auth.ts src/middleware.ts
/git:aipcc-commit-suggest

# Rewrite last commit message
/git:aipcc-commit-suggest 1

# Summarize last 5 commits for squash
/git:aipcc-commit-suggest 5
```

## Return Value

Generates 3 AIPCC-formatted commit message suggestions:
- **Suggestion #1 (Recommended)** – Detailed with full body and Jira integration
- **Suggestion #2 (Standard)** – Concise with essential information
- **Suggestion #3 (Minimal)** – Brief description with required elements

Each suggestion includes:
- AIPCC format title (`AIPCC-XXX: description`)
- Blank line between title and body
- Body text explaining the changes in complete sentences
- Optional Jira integration (`Fixes AIPCC-XXX`)
- Required sign-off line

**Example:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Suggestion #1 (Recommended)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AIPCC-123: Add JWT authentication middleware

Implement token-based authentication for API endpoints to enhance
security. The middleware verifies JWT tokens and extracts user
information for authorization decisions.

Fixes AIPCC-123

Co-Authored-By: [AI_NAME] ([AI_MODEL])

Signed-off-by: Your Name <your.email@example.com>

Which suggestion would you like to use? (1/2/3 or skip)
```

### Mode 2 Specifics

- **N=1** – Suggest improved rewrite for the last commit in AIPCC format
- **N≥2** – Generate unified AIPCC-formatted squash message with footer: `Squashed from N commits:` + original commit list

## Commit Message Format Requirements

### AIPCC Format
All commits must follow this project-specific format:
```
AIPCC-XXX: Short description

Longer explanation of what the commit does, written in at least one
complete sentence explaining the purpose and impact of the change.

[Optional: Fixes AIPCC-XXX]

[Optional: Co-Authored-By: [AI_NAME] ([AI_MODEL])]

Signed-off-by: Your Name <your.email@example.com>
```

### Required Elements
- **Title**: Must start with "AIPCC-XXX:" followed by a short description
- **Body**: Must explain what the commit does in at least one complete sentence
- **Sign-off**: All commits must include `Signed-off-by` line (use `git commit -s`)

### Optional Elements
- **Jira Integration**: Include "Fixes AIPCC-XXX" in the body to automatically close the Jira ticket when MR merges
- **Co-authors**: `Co-Authored-By: Name <email@example.com>`
- **AI Attribution**: `Co-Authored-By: [AI_NAME] ([AI_MODEL])` when AI assists with code generation
- **Breaking Changes**: Note significant API changes in the body

### Examples
```
AIPCC-456: Fix memory leak in authentication service

Resolve memory leak caused by unclosed database connections in the
auth service. This improves server stability under high load.

Fixes AIPCC-456

Co-Authored-By: [AI_NAME] ([AI_MODEL])

Signed-off-by: Jane Developer <jane@example.com>
```

```
AIPCC-789: Add user profile management API

Implement REST endpoints for user profile CRUD operations.
Includes validation, error handling, and comprehensive test coverage.

Co-Authored-By: [AI_NAME] ([AI_MODEL])

Signed-off-by: John Developer <john@example.com>
```

## Arguments

- **[N]** (optional): Number of recent commits to analyze (1-100)
  - If omitted: Analyzes staged changes (Mode 1)
  - If N=1: Suggests improved rewrite for the last commit
  - If N≥2: Generates unified squash message for last N commits

## See Also
- **`/git:summary`** – Display repository status and recent commits (read-only)
- **AIPCC Project Guidelines** – Internal project commit format requirements
- [Conventional Commits Specification](https://www.conventionalcommits.org/) – General industry standard (adapted for AIPCC format)
