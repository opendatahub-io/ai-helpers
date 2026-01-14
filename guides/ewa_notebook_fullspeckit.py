#!/usr/bin/env python3
"""
Agor + Speckit + Jira: Multi-Agent Specification-Driven Development
Interactive Presentation

Navigate through slides using the UI controls below.
"""

import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # Slide titles
    slide_titles = [
        "1. Title",
        "2. TL;DR",
        "3. The Problem",
        "4. The Solution",
        "5. What, Not How",
        "6. Human-in-the-Loop",
        "7. 7-Stage Workflow",
        "8. Stage 1: Setup",
        "9. Stage 2: Specify",
        "10. Stage 3: Clarify",
        "11. Stage 4: Plan",
        "12. Stage 5: Tasks",
        "13. Stage 6: Analyze",
        "14. Stage 7: Implement",
        "15. Agor Features",
        "16. Jira Integration",
        "17. Speckit Commands",
        "18. Architecture",
        "19. Best Practices",
        "20. Challenges & Wins",
        "21. Key Takeaways",
        "22. Resources"
    ]
    return (slide_titles,)


@app.cell
def _(mo, slide_titles):
    # Create slider control
    current_slide = mo.ui.slider(
        start=1,
        stop=len(slide_titles),
        value=1,
        label="Slide",
        show_value=True
    )
    return (current_slide,)


@app.cell
def _(current_slide, mo, slide_titles):
    # Navigation display
    navigation = mo.md(f"""
    ## Presentation Navigation

    **Current Slide:** {slide_titles[current_slide.value - 1]}

    {current_slide}
    """)
    navigation
    return


@app.cell
def _(current_slide, mo):
    # All slides in one cell - only render the current slide

    # Slide 1: Title
    if current_slide.value == 1:
        slide_content = mo.md(f"""
        <div style="text-align: center; padding: 60px 20px;">
            <svg width="300" height="100" viewBox="0 0 300 100" style="margin-bottom: 40px;">
                <text x="150" y="50" font-family="Arial, sans-serif" font-size="48" font-weight="bold"
                      fill="#EE0000" text-anchor="middle" dominant-baseline="middle">
                    Red Hat
                </text>
            </svg>

            <h1 style="color: #EE0000; font-size: 2.5em; margin-bottom: 20px;">
                Agor + Speckit + Jira
            </h1>

            <h2 style="color: #333; font-size: 1.8em; margin-bottom: 20px;">
                Multi-Agent Specification-Driven Development
            </h2>

            <p style="font-size: 1.3em; color: #666;">
                AI-Assisted Development with Structure and Scale
            </p>

            <hr style="width: 60%; margin: 40px auto; border: 2px solid #EE0000;">

            <p style="font-size: 1.1em; color: #888;">
                An attempt at an Agentic Engineering Workflow
            </p>
        </div>
        """)

    # Slide 2: TL;DR
    elif current_slide.value == 2:
        slide_content = mo.vstack([
            mo.md("# TL;DR\n\n## Humans Are the Bottleneck"),
            mo.callout(
                mo.md("""
                **The Challenge:** We—humans—are the bottleneck in the development process.

                **The Opportunity:** Let's find systematic ways to address this challenge using AI-assisted workflows.

                This presentation shows how to combine three tools (Agor, Speckit, Jira) to create a structured,
                repeatable process that amplifies human decision-making while delegating execution to AI.
                """),
                kind="info"
            )
        ])

    # Slide 3: The Problem
    elif current_slide.value == 3:
        slide_content = mo.vstack([
            mo.md("# The Problem\n\n## Traditional AI-Assisted Development Challenges"),
            mo.accordion({
                "🎯 Ad-hoc Prompting": mo.md("""
                - No structure or repeatability
                - Inconsistent results across team members
                - Difficult to share best practices
                """),
                "❓ Ambiguous Requirements → Rework Cycles": mo.md("""
                - Vague specs lead to wrong implementations
                - 3-5x time wasted on corrections
                - Burning context on clarifications instead of progress
                """),
                "🔀 Lost Context & Misaligned Implementation": mo.md("""
                - AI forgets earlier decisions
                - Implementation drifts from requirements
                - No single source of truth
                """),
                "😫 Review Fatigue ***": mo.md("""
                - Reviewing AI-generated code that solved the wrong problem
                - Endless back-and-forth catching misunderstandings late
                - Fundamental issues discovered during code review (too late!)
                """)
            })
        ])

    # Slide 4: The Solution
    elif current_slide.value == 4:
        slide_content = mo.vstack([
            mo.md("# The Solution: Three Tools\n\n## Agor / Speckit / Jira"),

            # Tool 1: Agor
            mo.callout(
                mo.md("""
                ### 🎨 Agor - Multi-Agent Canvas for Orchestration

                **Key Capabilities:**
                - 📊 Visual workflow management and session coordination
                - 🔀 Fork/spawn patterns for parallel AI work
                - 👥 Team collaboration with shared worktrees
                - 💾 Checkpoint and restore session capabilities

                **Learn More:** [agor.live](https://agor.live)
                """),
                kind="info"
            ),

            # Tool 2: Speckit
            mo.callout(
                mo.md("""
                ### 📋 Speckit - Structured Workflow Framework

                **Key Capabilities:**
                - ⚙️ 7-stage specification-driven development process
                - ⭐ 62,000+ GitHub stars - battle-tested workflow
                - 📝 Systematic transformation from requirements to code
                - 🎯 Constitution-based team standards enforcement

                **Learn More:** [github.com/github/spec-kit](https://github.com/github/spec-kit)
                """),
                kind="success"
            ),

            # Tool 3: Jira
            mo.callout(
                mo.md("""
                ### 🎫 Jira - Issue Tracking Integration

                **Key Capabilities:**
                - 🏢 Common platform for company requirements & prioritization
                - 🔗 Automatic ticket extraction from branch names
                - 📈 Draft PR creation and bidirectional linking
                - 📋 Context fetching (parent stories, subtasks, full history)

                **Status:** Company Standard Tool
                """),
                kind="neutral"
            ),

            # Integration diagram
            mo.md("""
            ---

            ### How They Work Together

            ```
            Jira Ticket → Agor Canvas → Speckit Workflow → Claude AI → Git Repository
                ↑                                                            ↓
                └────────────────── PR Updates ─────────────────────────────┘
            ```

            **The workflow:** Jira provides requirements → Agor orchestrates multiple AI sessions →
            Speckit enforces structured stages → Changes tracked in Git → Progress visible in Jira
            """)
        ])

    # Slide 5: What, Not How
    elif current_slide.value == 5:
        slide_content = mo.vstack([
            mo.md("# The \"What, Not How\" Principle\n\n## Critical Success Factor for AI-Assisted Development"),
            mo.callout(
                mo.md("""
                **Clarity about WHAT to build is the highest-leverage work in the entire workflow.**

                **For the HOW - build guardrails and constraints with common practices.**

                Outsource the _writing_ not the _thinking_.
                """),
                kind="warn"
            ),
            mo.md("""
            ### Vague vs. Clear Requirements

            | ❌ Vague (Causes Problems) | ✅ Clear (Enables Success) |
            |---------------------------|---------------------------|
            | "Add user authentication" | "Users must log in with email/password. Session expires after 24 hours. Failed attempts are rate-limited to 5 per minute." |
            | "Make it faster" | "Page load time must be under 2 seconds for 95th percentile users on 3G connections" |
            | "Handle errors better" | "All API errors return structured JSON with error code, message, and correlation ID. 4xx errors are logged at WARN, 5xx at ERROR" |
            | "Add tests" | "Unit test coverage must reach 80%. All public APIs require integration tests. Edge cases from acceptance criteria must have explicit test cases" |
            """),
            mo.callout(
                mo.md("""
                ### Front-Load the Thinking

                The Speckit workflow is designed to front-load clarity:

                1. **Specify** captures WHAT the feature does and WHY it matters
                2. **Clarify** surfaces ambiguities BEFORE technical decisions
                3. **Plan** translates clear requirements into HOW to build
                4. **Tasks** break the plan into executable units

                **Investing in Specify and Clarify stages isn't optional overhead—it's the highest-leverage work.**
                """),
                kind="success"
            )
        ])

    # Slide 6: Human-in-the-Loop
    elif current_slide.value == 6:
        slide_content = mo.vstack([
            mo.md("# Human-in-the-Loop Review Gates\n\n## AI Assists, Humans Decide - Speckit Workflow"),
            mo.md("""
            ```
            ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌──────┐     ┌───────┐     ┌─────────┐     ┌───────────┐
            │  Setup  │────▶│ Specify │────▶│ Clarify │────▶│ Plan │────▶│ Tasks │────▶│ Analyze │────▶│ Implement │
            └─────────┘     └────┬────┘     └────┬────┘     └──┬───┘     └───┬───┘     └────┬────┘     └─────┬─────┘
                                 │               │             │             │              │               │
                                 ▼               ▼             ▼             ▼              ▼               ▼
                             [REVIEW]        [REVIEW]      [REVIEW]      [REVIEW]       [REVIEW]        [REVIEW]
            ```
            """),
            mo.md("""
            ### What to Review at Each Stage

            | Stage | Review Focus | Key Questions |
            |-------|--------------|---------------|
            | **Specify** | Requirements accuracy | Does this capture the real need? Would stakeholders agree? |
            | **Clarify** | Completeness | Are all ambiguities resolved? Any remaining questions? |
            | **Plan** | Technical soundness | Is this the right approach? What are the risks? |
            | **Tasks** | Scope & granularity | Are tasks properly sized? Dependencies clear? |
            | **Analyze** | Consistency | Do spec, plan, and tasks align? Any gaps? |
            | **Implement** | Quality | Does code match plan? Tests passing? |
            """),
            mo.callout(
                mo.md("""
                ### Feedback Loop Options

                After review, you can:

                - **✅ Approve**: Proceed to the next stage
                - **📝 Revise**: Ask AI to update with your feedback
                - **🔄 Iterate**: Go back to a previous stage
                - **🔀 Fork**: Explore alternatives while preserving current approach

                **All stages are easily referenced and visible in the Agor canvas.**
                """),
                kind="info"
            )
        ])

    # Slide 7: 7-Stage Workflow
    elif current_slide.value == 7:
        slide_content = mo.vstack([
            mo.md("# The 7-Stage Workflow\n\n## Visual Overview"),
            mo.mermaid("""
            flowchart LR
                subgraph Stage1["1. Setup"]
                    S1A[Init Speckit]
                    S1B[Constitution]
                    S1C[Link Jira]
                    S1D[Create PR]
                    S1A --> S1B --> S1C --> S1D
                end

                subgraph Stage2["2. Specify"]
                    S2A[Fetch Context]
                    S2B[Write Spec]
                    S2A --> S2B
                end

                subgraph Stage3["3. Clarify"]
                    S3A[Identify Gaps]
                    S3B[Resolve Questions]
                    S3A --> S3B
                end

                subgraph Stage4["4. Plan"]
                    S4A[Commit WIP]
                    S4B[Tech Design]
                    S4A --> S4B
                end

                subgraph Stage5["5. Tasks"]
                    S5A[Generate Tasks]
                end

                subgraph Stage6["6. Analyze"]
                    S6A[Consistency]
                    S6B[Coverage]
                    S6A --> S6B
                end

                subgraph Stage7["7. Implement"]
                    S7A[Code]
                    S7B[Test]
                    S7C[Commit]
                    S7A --> S7B --> S7C
                end

                Stage1 --> Stage2 --> Stage3 --> Stage4 --> Stage5 --> Stage6 --> Stage7

                classDef setupStyle fill:#3B82F6,color:#fff
                classDef specStyle fill:#8B5CF6,color:#fff
                classDef clarifyStyle fill:#EC4899,color:#fff
                classDef planStyle fill:#F97316,color:#fff
                classDef taskStyle fill:#EAB308,color:#000
                classDef analyzeStyle fill:#22C55E,color:#fff
                classDef implementStyle fill:#06B6D4,color:#fff

                class Stage1 setupStyle
                class Stage2 specStyle
                class Stage3 clarifyStyle
                class Stage4 planStyle
                class Stage5 taskStyle
                class Stage6 analyzeStyle
                class Stage7 implementStyle
            """),
            mo.md("""
            ### Stages at a Glance

            1. **Setup** → repo/branch/Constitution
            2. **Specify** → Requirements/sync with Jira
            3. **Clarify** → Resolve Ambiguities
            4. **Plan** → Technical Design
            5. **Tasks** → Work Breakdown
            6. **Analyze** → Consistency Check
            7. **Implement** → Execution
            """)
        ])

    # Slides 8-14: Individual Stage Details
    elif current_slide.value == 8:
        slide_content = mo.vstack([
            mo.md("# Stage 1: Setup\n\n## Initialize Repository & Constitution"),
            mo.callout(
                mo.md("""
                ### What This Stage Does

                - 📄 Copy team's AGENT.md configuration
                - 📦 Sync Python dependencies with `uv sync`
                - ⚙️ Initialize Speckit with AI agent configuration
                - 📋 Copy team's constitution (coding standards & guidelines)
                - 🔗 Link current branch to Jira ticket
                - 🚀 Create draft PR if one doesn't exist

                ### Key Configuration Files

                ```
                .specify/
                ├── memory/
                │   └── constitution.md    # Coding standards and guidelines
                AGENT.md                   # AI Agent guidelines
                ```

                ### Session Behavior

                🔄 **always_new** - Creates fresh session every time
                """),
                kind="info"
            )
        ])

    elif current_slide.value == 9:
        slide_content = mo.vstack([
            mo.md("# Stage 2: Specify\n\n## Create Requirements Specification"),
            mo.callout(
                mo.md("""
                ### Purpose

                - Document feature requirements in structured format
                - Pull context from Jira tickets (including parent stories)
                - Focus on business value and user outcomes
                - **Avoid implementation details at this stage**

                ### Output

                Creates specification document in `.specify/specs/` that includes:

                - ✨ Feature overview and objectives
                - 📖 User stories or acceptance criteria
                - 💼 Business context and constraints
                - 🔗 Related documentation links

                ### Command

                ```bash
                /speckit.specify
                ```

                ### Session Behavior

                🔄 **always_new** - Fresh context for each specification
                """),
                kind="success"
            )
        ])

    elif current_slide.value == 10:
        slide_content = mo.vstack([
            mo.md("# Stage 3: Clarify\n\n## Resolve Ambiguities Before Planning"),
            mo.callout(
                mo.md("""
                ### Purpose

                - 🔍 Identify and resolve gaps in specification
                - ❓ Surface blocking questions early
                - 🛡️ Prevent wasted effort during implementation

                ### What Gets Clarified

                - Ambiguous acceptance criteria
                - Missing edge case definitions
                - Unclear business rules
                - Integration requirements
                - Performance expectations

                ### Command

                ```bash
                git commit -m "wip: pre-clarify cleanup" --no-verify
                /speckit.clarify
                ```

                ### Session Behavior

                🎯 **show_picker** - Choose existing or new session
                """),
                kind="warn"
            )
        ])

    elif current_slide.value == 11:
        slide_content = mo.vstack([
            mo.md("# Stage 4: Plan\n\n## Create Technical Implementation Plan"),
            mo.callout(
                mo.md("""
                ### Purpose

                - 🏗️ Design technical approach
                - 🔧 Identify components to modify or create
                - ⚠️ Consider edge cases and error handling
                - 📝 Document architectural decisions

                ### Best Practices

                1. **Clean git state**: Always commit WIP changes before planning
                2. **Reference the spec**: Plan should trace back to specification
                3. **Include test strategy**: How will we verify the implementation?
                4. **Identify risks**: Note areas of uncertainty

                ### Command

                ```bash
                git add . && git commit -m "wip: pre-plan cleanup"
                /speckit.plan
                ```

                ### Session Behavior

                🎯 **show_picker** - Allows reusing context from previous work
                """),
                kind="neutral"
            )
        ])

    elif current_slide.value == 12:
        slide_content = mo.vstack([
            mo.md("# Stage 5: Tasks\n\n## Break Plan Into Actionable Work"),
            mo.callout(
                mo.md("""
                ### Purpose

                - 📋 Create granular task list from plan
                - ⚡ Enable parallel work streams where possible
                - 👀 Make progress visible and trackable

                ### Task Quality Checklist

                Good tasks are:

                - **Atomic**: Completable in one focused session
                - **Testable**: Have clear completion criteria
                - **Independent**: Minimize dependencies on other tasks
                - **Sized appropriately**: Not too large, not too granular

                ### Command

                ```bash
                /speckit.tasks
                ```

                ### Session Behavior

                🎯 **show_picker** - May iterate on task breakdown
                """),
                kind="neutral"
            )
        ])

    elif current_slide.value == 13:
        slide_content = mo.vstack([
            mo.md("# Stage 6: Analyze\n\n## Cross-Artifact Consistency Check"),
            mo.callout(
                mo.md("""
                ### Purpose

                - ✅ Verify consistency across spec, plan, and tasks
                - 🔍 Identify gaps in coverage
                - ⚔️ Discover potential conflicts
                - 🎯 Validate implementation readiness

                ### What Gets Analyzed

                - Consistency across all artifacts
                - Coverage gaps (missing requirements)
                - Potential conflicts between tasks
                - Implementation readiness assessment

                ### Command

                ```bash
                /speckit.analyze
                ```

                ### Session Behavior

                🎯 **show_picker** - Review and iterate on findings
                """),
                kind="success"
            )
        ])

    elif current_slide.value == 14:
        slide_content = mo.vstack([
            mo.md("# Stage 7: Implement\n\n## Execute Implementation Tasks"),
            mo.callout(
                mo.md("""
                ### Purpose

                - 💻 Write code according to plan
                - 📋 Follow constitution guidelines
                - ✅ Maintain test coverage
                - 📚 Document as you go

                ### Implementation Guidelines

                1. **Follow the plan**: Stick to technical design
                2. **One task at a time**: Complete sequentially or parallelize with Agor
                3. **Test continuously**: Write tests alongside implementation
                4. **Commit frequently**: Small, atomic commits with clear messages

                ### Command

                ```bash
                /speckit.implement
                ```

                ### Session Behavior

                🎯 **show_picker** - Continue or start fresh implementation session
                """),
                kind="info"
            )
        ])

    # Slide 15: Agor Multi-Agent Features
    elif current_slide.value == 15:
        slide_content = mo.vstack([
            mo.md("# Agor Multi-Agent Features\n\n## Advanced Orchestration Capabilities"),
            mo.md("""
            ### Session Behaviors

            | Behavior | Description | Use Cases |
            |----------|-------------|-----------|
            | `always_new` | Creates fresh session every time | Setup, Specify stages that need clean starts |
            | `show_picker` | Prompts to choose existing or new | Clarify, Plan, Tasks, Analyze, Implement (may iterate) |
            """),
            mo.accordion({
                "🍴 Fork Sessions": mo.md("""
                **Creates a copy of current session with full context preserved**

                Use when:
                - Exploring alternative approaches
                - A/B testing implementations
                - Branching from a decision point

                Example: Try two different architectural approaches in parallel
                """),
                "🚀 Spawn Sessions": mo.md("""
                **Creates new independent session with selective context**

                Use when:
                - Parallel work on unrelated tasks
                - Delegating subtasks
                - Isolating concerns

                Example: Implement multiple independent features simultaneously
                """),
                "🎨 Visual Workflow Canvas": mo.md("""
                Agor provides:
                - Visual representation of session relationships
                - Progress tracking across stages
                - Context sharing between sessions
                - Checkpoint and restore capabilities
                """),
                "👥 Team Collaboration": mo.md("""
                - Share worktrees across team members
                - Collaborative session management
                - Environment configuration inheritance
                - Template variables for consistency
                """)
            })
        ])

    # Slide 16: Jira Integration
    elif current_slide.value == 16:
        slide_content = mo.vstack([
            mo.md("# Jira Integration\n\n## Common Platform for Company Requirements"),
            mo.callout(
                mo.md("""
                **Jira serves as the common platform for:**
                - 🏢 Company requirements and input
                - 📊 Prioritization and planning
                - 🔗 Automatic context fetching
                - 📈 Progress tracking and visibility
                """),
                kind="info"
            ),
            mo.mermaid("""
            sequenceDiagram
                participant Dev as Developer
                participant Git as Git Branch
                participant Agor as Agor Session
                participant Jira as Jira API
                participant GH as GitHub

                Dev->>Git: Create branch (jn-1234-feature)
                Dev->>Agor: Start Setup Session

                Agor->>Git: Extract ticket from branch name
                Git-->>Agor: JN-1234

                Agor->>Jira: Fetch ticket details
                Jira-->>Agor: Ticket info + parent story

                Agor->>Agor: Store {worktree.issue_url}

                Agor->>GH: Check for existing PR
                GH-->>Agor: No PR found

                Agor->>GH: Create Draft PR
                GH-->>Agor: PR URL

                Agor->>Agor: Store {worktree.pull_request_url}

                Note over Agor: Setup Complete
            """),
            mo.md("""
            ### Key Features

            - **Branch naming convention**: `jn-1234-feature-name`
            - **Automatic ticket extraction**: From branch name to Jira URL
            - **Draft PR creation**: Establish PR early for visibility
            - **Context fetching**: Pull parent stories, subtasks, and full context
            - **Bidirectional linking**: PR ↔ Jira ticket connection
            """)
        ])

    # Slide 17: Speckit Commands Reference
    elif current_slide.value == 17:
        slide_content = mo.vstack([
            mo.md("# Speckit Commands Reference\n\n## Common Platform for Specification-Driven Development"),
            mo.callout(
                mo.md("""
                **Speckit** is GitHub's specification-driven development framework with **over 62,000 GitHub stars**.

                It provides a battle-tested workflow for systematically transforming requirements into working software.
                """),
                kind="success"
            ),
            mo.mermaid("""
            flowchart TD
                subgraph Commands["Speckit Commands (Official Order)"]
                    direction LR

                    C1["/speckit.constitution<br/>━━━━━━━━━━━━━━━<br/>Create governing<br/>principles & guidelines"]

                    C2["/speckit.specify<br/>━━━━━━━━━━━━━━━<br/>Define requirements<br/>& user stories"]

                    C3["/speckit.clarify<br/>━━━━━━━━━━━━━━━<br/>Clarify underspecified<br/>areas before planning"]

                    C4["/speckit.plan<br/>━━━━━━━━━━━━━━━<br/>Create technical<br/>implementation plans"]

                    C5["/speckit.tasks<br/>━━━━━━━━━━━━━━━<br/>Generate actionable<br/>task lists"]

                    C6["/speckit.analyze<br/>━━━━━━━━━━━━━━━<br/>Cross-artifact<br/>consistency & coverage"]

                    C7["/speckit.implement<br/>━━━━━━━━━━━━━━━<br/>Execute all tasks<br/>to build the feature"]
                end

                C1 --> C2 --> C3 --> C4 --> C5 --> C6 --> C7

                classDef required fill:#10B981,color:#fff
                classDef optional fill:#6366F1,color:#fff

                class C1,C2,C4,C5,C7 required
                class C3,C6 optional
            """),
            mo.md("""
            ### Commands Quick Reference

            | Command | Required? | Purpose |
            |---------|-----------|---------|
            | `/speckit.constitution` | ✅ | Team coding standards & guidelines |
            | `/speckit.specify` | ✅ | Define what to build and why |
            | `/speckit.clarify` | 🔵 Optional | Resolve ambiguities early |
            | `/speckit.plan` | ✅ | Technical implementation design |
            | `/speckit.tasks` | ✅ | Actionable work breakdown |
            | `/speckit.analyze` | 🔵 Optional | Consistency verification |
            | `/speckit.implement` | ✅ | Execute the plan |
            """)
        ])

    # Slide 18: Architecture Overview
    elif current_slide.value == 18:
        slide_content = mo.vstack([
            mo.md("# Architecture Overview\n\n## Data Flow Between Layers"),
            mo.mermaid("""
            flowchart TB
                subgraph Layer1["Layer 1: Project Management"]
                    JIRA_TICKET["Jira Ticket<br/>Requirements & Context"]
                    DRAFT_PR["Draft PR<br/>Visibility & Review"]
                end

                subgraph Layer2["Layer 2: Orchestration"]
                    AGOR["Agor Canvas<br/>Multi-Agent Coordination"]
                end

                subgraph Layer3["Layer 3: Workflow Engine"]
                    SPECKIT["Speckit<br/>Structured Development Stages"]
                end

                subgraph Layer4["Layer 4: AI Assistant"]
                    CLAUDE["Claude Code<br/>AI-Powered Implementation"]
                end

                subgraph Layer5["Layer 5: Version Control"]
                    GIT["Git Repository<br/>Code & Documentation"]
                end

                JIRA_TICKET -->|"context"| AGOR
                AGOR -->|"creates"| DRAFT_PR
                AGOR -->|"orchestrates"| SPECKIT
                SPECKIT -->|"invokes"| CLAUDE
                CLAUDE -->|"commits"| GIT
                GIT -->|"linked to"| DRAFT_PR
                DRAFT_PR -->|"updates"| JIRA_TICKET

                classDef layer1 fill:#0052CC,color:#fff
                classDef layer2 fill:#6366F1,color:#fff
                classDef layer3 fill:#10B981,color:#fff
                classDef layer4 fill:#F59E0B,color:#fff
                classDef layer5 fill:#EF4444,color:#fff

                class JIRA_TICKET,DRAFT_PR layer1
                class AGOR layer2
                class SPECKIT layer3
                class CLAUDE layer4
                class GIT layer5
            """),
            mo.md("""
            ### Layer Responsibilities

            1. **Project Management**: Jira tracks requirements, PRs provide visibility
            2. **Orchestration**: Agor coordinates multiple AI sessions visually
            3. **Workflow Engine**: Speckit enforces structured development stages
            4. **AI Assistant**: Claude Code executes implementation with AI
            5. **Version Control**: Git stores all artifacts and code

            **Data flows bidirectionally**, ensuring all layers stay synchronized.
            """)
        ])

    # Slide 19: Best Practices
    elif current_slide.value == 19:
        slide_content = mo.vstack([
            mo.md("# Best Practices\n\n## Setting Up for Success"),
            mo.callout(
                mo.md("""
                ### Critical Foundation: Two Key Artifacts

                #### 1. Team Constitution Document

                A comprehensive `constitution.md` that captures:
                - Company coding standards and conventions
                - Team-specific architectural patterns
                - Technology stack decisions and rationale
                - Testing requirements and coverage expectations
                - Documentation standards
                - Code review guidelines
                - Security and compliance requirements

                #### 2. Well-Defined Jira Tickets

                Each ticket should contain:
                - Clear problem statement or feature description
                - **Specific, testable acceptance criteria**
                - Definition of Done (DoD) aligned with team standards
                - Relevant context, background, and business justification
                - Links to related tickets, documentation, or designs

                **The quality of these artifacts directly impacts the quality of AI-generated specs, plans, and code.**
                """),
                kind="warn"
            ),
            mo.accordion({
                "🎯 Catch Vague Requirements Up Front": mo.md("""
                - Review Jira tickets before starting workflow
                - Push back on vague acceptance criteria
                - Ask "How would we test this?" for each requirement
                - Ensure stakeholder alignment before Specify stage
                """),
                "👥 Review Specifications with Stakeholders": mo.md("""
                - After Specify stage, get stakeholder sign-off
                - Validate that spec captures true intent
                - Clarify business context and constraints
                - Document any assumptions made
                """),
                "🔄 Commit Before Stage Transitions": mo.md("""
                - Keep git clean between stages
                - Use WIP commits: `git commit -m "wip: pre-plan cleanup"`
                - Easier to track what changed in each stage
                - Simplifies rollback if needed
                """),
                "📋 Use Draft PRs Early": mo.md("""
                - Establish PR at Setup stage, not at the end
                - Enable early code review and feedback
                - Track progress visibly in Jira
                - Update PR description as spec evolves
                """)
            })
        ])

    # Slide 20: Challenges & Easy Wins
    elif current_slide.value == 20:
        slide_content = mo.vstack([
            mo.md("# Challenges & Easy Wins\n\n## What We've Learned"),
            mo.callout(
                mo.md("""
                ### ✅ Easy Wins - Start Here

                1. **Common AGENT.md with well-defined rules**
                   - Single source of truth for AI behavior
                   - Consistent across all team repositories
                   - Versioned and reviewed like code

                2. **Well-thought-out constitution.md for team and repo**
                   - Captures institutional knowledge
                   - Reduces "how do we do X?" questions
                   - Improves AI-generated code quality immediately

                3. **Technical design should have more guidance from repo standards**
                   - Include architecture decision records (ADRs)
                   - Document common patterns and anti-patterns
                   - Provide examples of good implementations
                """),
                kind="success"
            ),
            mo.accordion({
                "⚠️ Challenge: Initial Setup Time": mo.md("""
                **Problem**: Creating constitution.md and AGENT.md takes time

                **Mitigation**:
                - Start with template and iterate
                - Extract rules from existing code reviews
                - Build incrementally as patterns emerge
                """),
                "⚠️ Challenge: Team Adoption": mo.md("""
                **Problem**: Learning curve for new workflow

                **Mitigation**:
                - Start with one team or project
                - Create runbook/cheat sheet
                - Pair programming to teach workflow
                - Share success stories
                """),
                "⚠️ Challenge: Keeping Artifacts in Sync": mo.md("""
                **Problem**: Constitution and standards drift over time

                **Mitigation**:
                - Treat as living documents
                - Review during retrospectives
                - Update when patterns change
                - Version control all artifacts
                """),
                "⚠️ Challenge: Balancing Automation vs Control": mo.md("""
                **Problem**: When to let AI run vs when to intervene

                **Mitigation**:
                - Use review gates religiously
                - Fork sessions when uncertain
                - Trust but verify at each stage
                - Build team judgment over time
                """)
            })
        ])

    # Slide 21: Key Takeaways
    elif current_slide.value == 21:
        slide_content = mo.vstack([
            mo.md("# Key Takeaways\n\n## What to Remember"),
            mo.callout(
                mo.md("""
                ### 🎯 Transforms Ad-Hoc AI Prompting into Structured Process

                Move from "hope the AI understands" to systematic, repeatable workflow with clear stages and checkpoints.
                """),
                kind="success"
            ),
            mo.callout(
                mo.md("""
                ### 📊 Front-Load Clarity to Reduce Rework

                Investing in Specify and Clarify stages prevents 3-5x rework downstream.
                The highest-leverage work is defining WHAT to build, not HOW to build it.
                """),
                kind="success"
            ),
            mo.callout(
                mo.md("""
                ### 👥 Human Review Gates at Every Stage

                AI assists, humans decide. Each stage transition is a deliberate checkpoint where you review,
                validate, and approve before proceeding. All stages are visible and easily referenced.
                """),
                kind="success"
            ),
            mo.callout(
                mo.md("""
                ### 🔄 Multi-Agent Orchestration Scales Work

                Agor's fork/spawn patterns enable parallel execution while maintaining context and consistency.
                Visual canvas makes complex workflows manageable.
                """),
                kind="info"
            ),
            mo.callout(
                mo.md("""
                ### 📝 Context Preservation Throughout Workflow

                Jira integration, draft PRs, and staged artifacts create single source of truth.
                No more lost context or misaligned implementations.
                """),
                kind="info"
            )
        ])

    # Slide 22: Resources
    elif current_slide.value == 22:
        slide_content = mo.vstack([
            mo.md("# Resources & Next Steps\n\n## Get Started Today"),
            mo.md("""
            ### 🔗 Tool Links

            - **Agor**: [agor.live](https://agor.live)
              - Multi-agent orchestration canvas
              - [Advanced Features Guide](https://agor.live/guide/advanced-features)

            - **Speckit**: [github.com/github/spec-kit](https://github.com/github/spec-kit)
              - 62K+ stars
              - Specification-driven development framework

            - **Claude Code**: [Anthropic Documentation](https://docs.anthropic.com/claude-code)
              - AI-powered development assistant
            """),
            mo.md("""
            ### 📚 Documentation

            - **Workflow Guide**: `guides/agor-speckit-workflow.md`
            - **Templates**: `guides/agor-speckit-templates.md`
            - **Diagrams**: `guides/agor-speckit-workflow-diagram.md`
            """),
            mo.callout(
                mo.md("""
                ### 🚀 Getting Started

                1. **Create your constitution.md** - Document team standards
                2. **Set up AGENT.md** - Define AI behavior rules
                3. **Pick a Jira ticket** - Choose well-defined requirement
                4. **Run through Setup stage** - Initialize Speckit + Agor
                5. **Follow the 7 stages** - Trust the process

                **Start small, iterate, and scale what works.**
                """),
                kind="success"
            ),
            mo.md("""
            ---

            <div style="text-align: center; padding: 20px;">
                <svg width="200" height="70" viewBox="0 0 200 70" style="margin-bottom: 20px;">
                    <text x="100" y="35" font-family="Arial, sans-serif" font-size="32" font-weight="bold"
                          fill="#EE0000" text-anchor="middle" dominant-baseline="middle">
                        Red Hat
                    </text>
                </svg>
                <p style="color: #666;">An Attempt at an Engineering Workflow Automation</p>
            </div>
            """)
        ])

    else:
        slide_content = mo.md("## Invalid slide number")

    slide_content
    return


@app.cell
def _():
    # End of presentation
    return


if __name__ == "__main__":
    app.run()
