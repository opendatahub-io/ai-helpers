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
        "4. What, Not How",
        "5. The Solution",
        "6. Human-in-the-Loop",
        "7. Architecture",
        "8. 7-Stage Workflow",
        "9. Best Practices",
        "10. Challenges & Path to Success",
        "11. Key Takeaways",
        "12. Resources"
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
def _(mo):
    # Apply presentation-friendly CSS styling
    presentation_css = mo.Html("""
    <style>
        /* Global font scaling for presentation */
        .marimo {
            font-size: 200% !important;
            line-height: 1.6 !important;
        }

        /* Headings - extra large */
        h1 {
            font-size: 3.5em !important;
            margin-bottom: 0.5em !important;
            line-height: 1.2 !important;
        }

        h2 {
            font-size: 2.5em !important;
            margin-bottom: 0.4em !important;
            line-height: 1.3 !important;
        }

        h3 {
            font-size: 2em !important;
            margin-bottom: 0.3em !important;
            line-height: 1.3 !important;
        }

        /* Paragraph and list text */
        p, li {
            font-size: 1.5em !important;
            margin-bottom: 0.8em !important;
            line-height: 1.6 !important;
        }

        /* Callout boxes */
        .callout {
            font-size: 1.4em !important;
            padding: 1.5em !important;
            margin: 1em 0 !important;
        }

        /* Code blocks */
        code, pre {
            font-size: 1.3em !important;
            line-height: 1.5 !important;
        }

        /* Tables */
        table {
            font-size: 1.4em !important;
        }

        th, td {
            padding: 0.8em !important;
        }

        /* Accordion headers */
        .accordion summary {
            font-size: 1.5em !important;
            padding: 0.8em !important;
        }

        /* Mermaid diagrams - larger */
        .mermaid {
            transform: scale(1.5) !important;
            transform-origin: top left !important;
            margin: 2em 0 !important;
        }

        /* Bullet points larger */
        ul, ol {
            margin-left: 1.5em !important;
        }

        /* Strong/bold text */
        strong, b {
            font-weight: 700 !important;
        }

        /* Links */
        a {
            font-size: 1.4em !important;
        }
    </style>
    """)
    presentation_css
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

    # Slide 5: The Solution
    elif current_slide.value == 5:
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

    # Slide 7: Architecture Overview
    elif current_slide.value == 7:
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

    # Slide 8: 7-Stage Workflow
    elif current_slide.value == 8:
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

    # Slide 9: Best Practices
    elif current_slide.value == 9:
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

    # Slide 10: Challenges & Easy Wins
    elif current_slide.value == 10:
        slide_content = mo.vstack([
            mo.md("# Challenges & Path to Success\n\n## What We've Learned"),
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

    # Slide 11: Key Takeaways
    elif current_slide.value == 11:
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

    # Slide 12: Resources
    elif current_slide.value == 12:
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
