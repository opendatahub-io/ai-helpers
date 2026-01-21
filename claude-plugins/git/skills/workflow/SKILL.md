---
name: workflow
description: Proactive git workflow automation with checkpoint commits and history cleanup
allowed-tools: [Bash, Read, Grep, Glob, AskUserQuestion, Skill]
---

# Git Workflow Automation Skill

This skill enables proactive git workflow management during development sessions. It monitors work progress and offers intelligent git operations at appropriate moments.

## When to Activate This Skill

Activate this workflow when you detect:
- User is about to start a **substantial change** (multi-file edits, new features, refactoring)
- User describes a task that will require **multiple steps** or iterations
- User explicitly mentions wanting to **track progress** or maintain clean history
- The conversation involves **implementation work** rather than just exploration

## Key Behaviors

### 1. Branch Management (Start of Work)

**Detection signals:**
- User describes a new feature or significant change
- Task involves modifying core functionality
- User mentions "implement", "add", "refactor", "fix" for non-trivial changes

**Action:**
Ask the user (using AskUserQuestion) whether they want to:
- Create a new feature branch (suggest a name based on the task)
- Continue on the current branch

**Example prompt:**
> This looks like a substantial change. Would you like me to create a feature branch for this work, or continue on the current branch?

Only ask once at the start of a work session. Don't repeatedly ask about branches.

### 2. Checkpoint Commits (During Work)

**When to offer a checkpoint commit:**
- After completing a logical unit of work (function, component, module)
- After fixing a bug or resolving an error
- Before making a significant architectural change
- After ~15-20 minutes of continuous work with uncommitted changes
- When switching focus to a different part of the codebase

**Detection signals:**
- Multiple files have been modified
- A feature or fix is working but work continues
- User says "ok", "good", "that works", "next" suggesting a milestone

**Action:**
Proactively offer to create a checkpoint commit:
> I've made several changes to the authentication module. Would you like me to create a checkpoint commit to save this progress?

If the user agrees, invoke `/git:commit dev` to create a verbose development commit.

**Important:**
- Don't interrupt flow for every small change
- Batch related changes into logical checkpoints
- Always use `dev` style for checkpoint commits (preserves context)

### 3. Completion Detection (End of Work)

**Detection signals:**
- User expresses satisfaction: "looks good", "that's it", "perfect", "done"
- User asks about next steps or other tasks
- All requested changes have been implemented
- Tests pass (if applicable)
- User mentions PR, merge, or pushing

**Action:**
Summarize the work done and offer history cleanup:
> I've completed the authentication refactoring. We have 5 development commits. Would you like me to:
> 1. Clean up the commit history (squash into cohesive commits with `/git:merge`)
> 2. Keep the detailed development history as-is
> 3. Push the current state and clean up later

### 4. History Cleanup (When Requested)

**When user wants cleanup:**
- Analyze the commit range to determine logical groupings
- Suggest how to combine commits (which ones belong together)
- Offer style transformation (dev → final)

**Example workflow:**
```
We have 6 commits:
- 3 related to OAuth implementation
- 2 related to token validation
- 1 documentation update

I suggest:
1. Merge the 3 OAuth commits into one
2. Merge the 2 token validation commits into one
3. Keep the docs commit separate

Want me to proceed with this cleanup?
```

Use `/git:merge` with appropriate count/SHA and style arguments.

After merging, offer `/git:reword` if commit messages need refinement.

## Workflow State Tracking

Maintain awareness of:
- **Current branch**: Feature branch vs main/development branch
- **Uncommitted changes**: Files modified since last commit
- **Commit count**: Number of commits since branch creation or session start
- **Work phase**: Starting / In-progress / Wrapping up

Use `git status`, `git log`, and `git diff --stat` to assess state when needed.

## Non-Intrusive Guidelines

**DO:**
- Ask permission before any git operation
- Explain what operation will do before executing
- Suggest appropriate timing for commits
- Adapt to user's workflow preferences

**DON'T:**
- Interrupt mid-thought or mid-implementation
- Force workflow on users who decline
- Create commits without explicit approval
- Pester repeatedly if user declines offers

**Remember user preferences:**
- If user declines branch creation, don't ask again this session
- If user prefers manual commits, reduce checkpoint offers
- Match frequency of offers to user's apparent preference

## Integration with Git Commands

This skill orchestrates the following commands:
- `/git:commit dev` - Checkpoint commits during development
- `/git:commit final` - Clean commits for completed work
- `/git:merge N [style]` - Squash related commits
- `/git:reword SHA [style]` - Refine commit messages

Always invoke these commands using the Skill tool rather than reimplementing their logic.

## Example Session Flow

```
User: "I need to add OAuth authentication to the app"

[Branch Management]
Claude: "This is a substantial feature. Would you like me to create a
        feature branch like 'feature/oauth-authentication'?"
User: "Yes"
Claude: [Creates branch]

[Development with Checkpoints]
Claude: [Implements OAuth provider setup]
Claude: "OAuth provider configuration is complete. Want me to checkpoint
        this progress?"
User: "Sure"
Claude: [Invokes /git:commit dev]

Claude: [Implements token handling]
Claude: [Implements session management]
Claude: "Token handling and session management are working. Checkpoint?"
User: "Yes"
Claude: [Invokes /git:commit dev]

[Completion]
User: "Looks good, that's everything"
Claude: "Great! We have 4 development commits on this branch:
        - OAuth provider setup
        - Token handling implementation
        - Session management
        - Final integration fixes

        Would you like me to clean these up before merging? I can
        combine them into 1-2 clean commits."
User: "Yes, make it one commit"
Claude: [Invokes /git:merge 3 final]
Claude: "Done! Here's the final commit message: [shows message]
        Want me to adjust it?"
```
