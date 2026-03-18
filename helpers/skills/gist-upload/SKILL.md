---
name: gist-upload
description: Upload a summary or plan from the current conversation as a GitHub Gist using the `gh` CLI.
allowed-tools: Bash
---

# Upload to GitHub Gist

Upload content from the current conversation (a plan, summary, analysis, or other output) as a GitHub Gist using the `gh` CLI.

## Prerequisites

- `gh` CLI must be installed and authenticated (`gh auth status` should succeed)

## Usage

This skill triggers when the user asks to upload conversation content to a gist, for example:
- "Upload the plan to gist"
- "Upload the summary of our conversation as a gist"
- "Create a gist with the analysis above"
- "Share this as a gist"

## Implementation

### Step 1: Identify the Content

1. Look at the conversation history to identify what the user wants uploaded
2. If the user says "the plan", "the summary", "the analysis", etc., find that specific content in the conversation
3. If ambiguous, ask the user: "Which part of our conversation should I upload? For example, the plan, summary, or a specific section?"

### Step 2: Format the Content

1. Take the identified content and format it as clean markdown
2. Choose a descriptive filename based on the content type, e.g. `plan.md`, `summary.md`, `analysis.md`
3. If the content relates to a specific project or topic, include that in the filename, e.g. `migration-plan.md`

### Step 3: Upload via `gh gist create`

1. Write the content to a temporary file in `/tmp/`
2. Upload using `gh`:
   ```bash
   gh gist create /tmp/<filename>
   ```
   - Gists are created as **secret** by default. Note: secret gists are **unlisted, not private**, anyone with the URL can view them. Warn the user about this before uploading sensitive content.
   - If the user explicitly asks for a public gist, add `--public`
3. Capture the gist URL from the command output

### Step 4: Report and Clean Up

1. Show the user the gist URL
2. Delete the temporary file
