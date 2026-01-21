# Agor + Speckit: Multi-Agent Specification-Driven Development

A comprehensive guide to orchestrating AI-assisted development using Agor's multi-agent canvas, Speckit's specification-driven workflow, and Jira integration.

> **Reference**: Based on [GitHub Spec-Kit](https://github.com/github/spec-kit) workflow stages.

## Overview

This workflow combines three powerful tools to create a structured, AI-assisted development process:

- **[Agor](https://agor.live)**: Multi-agent canvas for coordinating AI sessions with visual workflow management
- **[Speckit](https://github.com/github/spec-kit)**: Specification-driven development workflow for systematic AI-assisted implementation
- **Jira**: Issue tracking and project management integration

The result is a repeatable, documented development process where AI assists at every stage—from understanding requirements through implementation.

## Prerequisites

### Technical Prerequisites

Tools and access required to run the workflow:

- **Agor account**: Access to [agor.live](https://agor.live) for multi-agent orchestration
- **AI agent**: e.g. Claude Code Anthropic's CLI installed and configured
- **Speckit**: Installed via `uv tool install specify-cli --from ...`
- **Jira access**: mcp server configured to read ticket
- **Git access**: via mcp or gh cli
- **Git repository**: A project repository


### Conceptual Prerequisites

Preparation and artifacts that maximize workflow effectiveness:

- **Well-defined Jira ticket**: The ticket should contain:
  - Clear problem statement or feature description
  - Acceptance criteria with specific, testable conditions
  - Definition of Done (DoD) aligned with team standards
  - Relevant context, background, and business justification
  - Links to related tickets, documentation, or designs


- **Team constitution**: A `constitution.md` file that captures:
  - Company coding standards and conventions
  - Team-specific architectural patterns and preferences
  - Technology stack decisions and rationale
  - Testing requirements and coverage expectations
  - Documentation standards
  - Code review guidelines
  - Security and compliance requirements

> **Tip**: The quality of your Jira ticket and constitution directly impacts the quality of AI-generated specifications, plans, and code. Invest time upfront in these artifacts to reduce rework downstream.

## The "What, Not How" Principle

**The most critical success factor for AI-assisted development is clarity about WHAT to build, not HOW to build it.**

### Why This Matters

AI agents are powerful executors but require precise direction. When requirements are vague or ambiguous, AI will fill in the gaps with assumptions—often reasonable ones, but not necessarily aligned with your intent. This leads to:

- **Slop**: Code that technically works but misses the actual need
- **Rework cycles**: Multiple rounds of "that's not quite what I meant"
- **Review fatigue**: Endless back-and-forth catching misunderstandings late
- **Wasted context**: Burning through conversation context on corrections instead of progress

### The Cost of Ambiguity

Every hour spent clarifying requirements upfront saves X3-5 hours of:
- Reviewing AI-generated code that solved the wrong problem
- Explaining why the implementation doesn't match expectations
- Refactoring code that was built on incorrect assumptions
- Re-running the entire workflow after discovering a fundamental misunderstanding

### What "Clarity" Means in Practice

| Vague (Causes Problems) | Clear (Enables Success) |
|-------------------------|-------------------------|
| "Add user authentication" | "Users must log in with email/password. Session expires after 24 hours. Failed attempts are rate-limited to 5 per minute." |
| "Make it faster" | "Page load time must be under 2 seconds for 95th percentile users on 3G connections" |
| "Handle errors better" | "All API errors return structured JSON with error code, message, and correlation ID. 4xx errors are logged at WARN, 5xx at ERROR" |
| "Add tests" | "Unit test coverage must reach 80%. All public APIs require integration tests. Edge cases from acceptance criteria must have explicit test cases" |

### Front-Load the Thinking

The Speckit workflow is designed to front-load clarity:

1. **Specify** captures WHAT the feature does and WHY it matters
2. **Clarify** surfaces ambiguities BEFORE technical decisions
3. **Plan** translates clear requirements into HOW to build
4. **Tasks** break the plan into executable units

If you find yourself frequently correcting AI output during implementation, the problem is almost always upstream—in the specification or clarification stages, not in the AI's capabilities.


Investing in the Specify and Clarify stages isn't optional overhead—it's the highest-leverage work in the entire workflow.

## Human-in-the-Loop: Review Gates

**AI assists, but humans decide.** Each stage transition is a deliberate checkpoint where you review, validate, and approve before proceeding.

### Why Review Gates Matter

AI-generated artifacts—specifications, plans, tasks, and code—are drafts, not final products. Without human review:

- Misunderstandings compound across stages
- Small errors in specifications become large errors in implementation
- AI assumptions go unchallenged until code review (too late)
- You lose the opportunity to course-correct early

### The Review Cadence

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌──────┐     ┌───────┐     ┌─────────┐     ┌───────────┐
│  Setup  │────▶│ Specify │────▶│ Clarify │────▶│ Plan │────▶│ Tasks │────▶│ Analyze │────▶│ Implement │
└─────────┘     └────┬────┘     └────┬────┘     └──┬───┘     └───┬───┘     └────┬────┘     └─────┬─────┘
                     │               │             │             │              │               │
                     ▼               ▼             ▼             ▼              ▼               ▼
                 [REVIEW]        [REVIEW]      [REVIEW]      [REVIEW]       [REVIEW]        [REVIEW]
                 Is the spec     Are all       Does the      Are tasks      Is everything   Does the code
                 complete?       questions     plan make     actionable?    consistent?     meet spec?
                                 answered?     sense?
```

### What to Review at Each Stage

| Stage | Review Focus | Key Questions |
|-------|--------------|---------------|
| **Specify** | Requirements accuracy | Does this capture the real need? Is anything missing? Would stakeholders agree? |
| **Clarify** | Completeness | Are all ambiguities resolved? Any remaining questions? |
| **Plan** | Technical soundness | Is this the right approach? Are there better alternatives? What are the risks? |
| **Tasks** | Scope and granularity | Are tasks properly sized? Dependencies clear? Anything missing? |
| **Analyze** | Consistency | Do spec, plan, and tasks align? Any gaps or conflicts? |
| **Implement** | Quality | Does the code match the plan? Tests passing? Constitution followed? |

### How to Provide Effective Feedback

When reviewing AI-generated artifacts:

1. **Be specific**: "The error handling section is missing retry logic" not "This needs more detail"
2. **Reference the source**: "The Jira ticket says X, but the spec says Y"
3. **Explain the why**: "This approach won't work because our database doesn't support..."
4. **Suggest alternatives**: "Consider using X instead of Y because..."

### The Feedback Loop

After review, you can:

- **Approve**: Proceed to the next stage
- **Revise**: Ask the AI to update the current artifact with your feedback
- **Iterate**: Go back to a previous stage if fundamental issues are discovered
- **Fork**: Explore an alternative approach while preserving the current one

### When to Involve Others

Some reviews benefit from additional perspectives:

- **After Specify**: Get stakeholder sign-off on requirements
- **After Plan**: Technical review from senior engineers or architects
- **After Implement**: Standard code review process

> **Key Insight**: The structured stages create natural pause points for thoughtful human review. Rushing through reviews defeats the purpose of the workflow—the goal is to catch issues early, not to move fast through stages.

## Quick Start: Import Agor Board

To get started quickly, import the pre-configured Agor board with all workflow zones:

### Importing the Board Template

1. **Download the board template**: [example-speckit.agor-board.yaml](example-speckit.agor-board.yaml)

2. **Import into Agor**:
   ```bash
   # Using Agor CLI
   agor board import example-speckit.agor-board.yaml
   ```

   Or via the Agor UI:
   - Open Agor (`agor open`)
   - Navigate to Boards
   - Click "Import Board"
   - Select the `example-speckit.agor-board.yaml` file

3. **Verify the import**: The board includes pre-configured zones for:
   - Initial spec-kit setup
   - Specify (requirements)
   - Clarify (resolve ambiguities)
   - Plan (technical design)
   - Tasks (work breakdown)
   - Analyze (consistency check)
   - Implement
   - Code Review
   - PR Comment Review
   - Find Jira Tickets

Each zone has trigger templates pre-configured with the appropriate Speckit commands and workflow steps.

## Workflow Architecture

> **Visual Diagrams**: For detailed interactive Mermaid diagrams, see [agor-speckit-workflow-diagram.md](agor-speckit-workflow-diagram.md)
>
> **Agor Templates**: For ready-to-use Agor board templates, see [agor-speckit-templates.md](agor-speckit-templates.md)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            AGOR CANVAS                                  │
│  ┌────────┐ ┌─────────┐ ┌─────────┐ ┌──────┐ ┌───────┐ ┌─────────────┐  │
│  │ Setup  │→│ Specify │→│ Clarify │→│ Plan │→│ Tasks │→│Analyze/Impl │  │
│  └────────┘ └─────────┘ └─────────┘ └──────┘ └───────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
        ↓           ↓           ↓          ↓        ↓           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          SPECKIT STAGES                                 │
│  constitution → specify → clarify → plan → tasks → analyze → implement  │
└─────────────────────────────────────────────────────────────────────────┘
        ↓           ↓           ↓          ↓        ↓           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         JIRA CONTEXT                                    │
│           Issue Linking ← Context Fetching → PR Creation                │
└─────────────────────────────────────────────────────────────────────────┘
```

## Stage 1: Initial Setup (Constitution)

The first stage initializes Speckit in your project, establishes governing principles, and sets up the Jira connection.
Create a _New Worktree_ linked to a Git repository and Jira Issue.

### What This Stage Does

1. Copies the _team's_ AGENT.md configuration
2. Syncs Python dependencies with `uv sync`
3. Initializes Speckit with AI AGENT configuration
4. Copies the _team's_ project constitution (coding standards and guidelines)
5. Links the current branch to its Jira ticket
6. Creates a draft PR if one doesn't exist

### Key Configuration Files

After setup, your project will have speckit skills available with the _teams_ constitution configured:

```
.specify/
├── memory/
│   └── constitution.md    # Coding standards and guidelines
AGENT.md                   # AI Agent ghuildings
```

> **Template**: See [Stage 1: Setup](agor-speckit-templates.md#stage-1-setup) for the Agor template.

## Stage 2: Specify (Requirements)

Create a specification document that captures the **what** and **why** of the feature.

### Purpose

- Document the feature requirements in a structured format
- Pull context from Jira tickets (including parent stories for subtasks)
- Focus on business value and user outcomes
- Avoid implementation details at this stage


### Output

Creates a specification document in `.specify/specs/` that includes:

- Feature overview and objectives
- User stories or acceptance criteria
- Business context and constraints
- Related documentation links

> **Template**: See [Stage 2: Specify](agor-speckit-templates.md#stage-2-specify) for the Agor template.

## Stage 3: Clarify (Resolve Ambiguities)

Clarify underspecified areas in the specification before planning. This is a recommended step that prevents wasted effort during implementation.

### Purpose

- Identify and Resolve gaps or ambiguities in the specification
- Surface blocking questions early


> **Template**: See [Stage 3: Clarify](agor-speckit-templates.md#stage-3-clarify) for the Agor template.

## Stage 4: Plan (Technical Design)

Create a technical implementation plan based on the clarified specification.

### Purpose

- Design the technical approach
- Identify components to modify or create
- Consider edge cases and error handling
- Document architectural decisions

### Best Practices

1. **Clean git state**: Always commit WIP changes before planning
2. **Reference the spec**: The plan should trace back to specification items
3. **Consider testing**: Include test strategy in the plan
4. **Identify risks**: Note areas of uncertainty

> **Template**: See [Stage 4: Plan](agor-speckit-templates.md#stage-4-plan) for the Agor template.

## Stage 5: Tasks (Work Breakdown)

Break the plan into discrete, actionable tasks.

### Purpose

- Create a granular task list from the plan
- Enable parallel work streams where possible
- Make progress visible and trackable


> **Template**: See [Stage 5: Tasks](agor-speckit-templates.md#stage-5-tasks) for the Agor template.

## Stage 6: Analyze (Cross-Artifact Consistency)

Perform cross-artifact analysis to ensure consistency and coverage before implementation.

### Purpose

- Verify consistency across spec, plan, and tasks
- Identify gaps in coverage
- Discover potential conflicts
- Validate implementation readiness


> **Template**: See [Stage 6: Analyze](agor-speckit-templates.md#stage-6-analyze) for the Agor template.

## Stage 7: Implement

Execute the implementation tasks.

### Purpose

- Write the code according to plan
- Follow constitution guidelines
- Maintain test coverage
- Document as you go


> **Template**: See [Stage 7: Implement](agor-speckit-templates.md#stage-7-implement) for the Agor template.

## Multi-Agent Orchestration with Agor

### Session Behaviors

- **always_new**: Start fresh session (used for setup, specify)
- **show_picker**: Choose existing or new session (used for clarify, plan, tasks, analyze, implement)

### Visual Workflow

Agor's canvas provides:

- Visual representation of session relationships
- Progress tracking across stages
- Context sharing between sessions
- Checkpoint and restore capabilities

## Agor Advanced Features

For complex development scenarios, Agor provides advanced capabilities that extend beyond basic session management.

> **Full Documentation**: See [Agor Advanced Features Guide](https://agor.live/guide/advanced-features) for complete details.

### Forked Sessions vs. Spawned Sessions

Agor supports two patterns for creating related sessions:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Fork** | Creates a copy of the current session with full context preserved | Exploring alternative approaches, A/B testing implementations, branching from a decision point |
| **Spawn** | Creates a new independent session with selective context | Parallel work on unrelated tasks, delegating subtasks, isolating concerns |

**When to Fork:**
- You want to try an alternative approach without losing your current progress
- You need to explore "what if" scenarios from a specific point
- You want to compare two different implementation strategies

**When to Spawn:**
- You need parallel execution of independent tasks
- You want to isolate a subtask to avoid polluting the main session's context
- You're delegating work that doesn't need the full parent context

### Environment Configuration

Agor allows configuring environment variables and settings that persist across sessions in a worktree:

- **Worktree Variables**: Store project-specific values like `{worktree.issue_url}` and `{worktree.pull_request_url}`
- **Session Inheritance**: Child sessions can inherit environment from parent sessions
- **Template Variables**: Use variables in templates that get resolved at session creation time

Common environment configurations:
- Jira ticket URLs and project keys
- Git remote and branch information
- API endpoints and credentials references
- Team-specific tool configurations


## Jira Integration Details

### Branch Naming Convention

Use Jira ticket prefixes in branch names:

```
jn-3767-post-processing-db     # Correct: JN-3767 extracted
feature/jn-3767-new-feature    # Correct: JN-3767 extracted
jn-3767                        # Correct: minimal format
```

### Automatic Linking

The workflow automatically:

1. Extracts Jira ticket from branch name
2. Fetches ticket details and parent story context
3. Creates draft PRs with ticket reference
4. Links PRs to Jira tickets

### PR Creation

Draft PRs are created automatically to:

- Establish the PR early for visibility
- Enable early code review
- Track progress in Jira


### Best Practices

1. **Commit before stage transitions**: Keep git clean between stages
2. **Use draft PRs**: Establish PR early, not at the end
3. **Clarify before planning**: Resolve ambiguities early to avoid rework
4. **Analyze before implementing**: Catch inconsistencies before coding
5. **Document decisions**: Capture why, not just what
6. **Review specifications**: Get buy-in before planning
7. **Parallelize wisely**: Use Agor for truly independent tasks

### Getting Help

- **Speckit documentation**: [GitHub repository](https://github.com/github/spec-kit)
- **Agor support**: [agor.live](https://agor.live)
- **Claude Code**: `/help` command or [documentation](https://docs.anthropic.com/claude-code)

## Summary

This workflow transforms AI-assisted development from ad-hoc prompting into a structured, repeatable process:

1. **Setup**: Initialize environment, create constitution, establish Jira connection
2. **Specify**: Document requirements (what and why)
3. **Clarify**: Resolve ambiguities and underspecified areas
4. **Plan**: Design technical approach
5. **Tasks**: Break down into actionable items
6. **Analyze**: Verify cross-artifact consistency and coverage
7. **Implement**: Execute with AI assistance

The combination of Agor's multi-agent orchestration, Speckit's structured stages, and Jira integration creates a powerful development workflow that maintains context, ensures quality, and provides visibility throughout the process.
