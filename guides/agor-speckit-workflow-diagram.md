# Agor + Speckit Workflow Diagram

Interactive Mermaid diagram showing the complete Agor → Speckit → Jira workflow.

> **Reference**: Based on [GitHub Spec-Kit](https://github.com/github/spec-kit) workflow stages.

## Simplified Stage Flow

```mermaid
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
```

## Speckit Command Reference

```mermaid
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
```

## Data Flow Between Layers

```mermaid
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
```

## Jira Integration Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Branch
    participant Agor as Agor Session
    participant Jira as Jira API
    participant GitHub as GitHub/GitLab

    Dev->>Git: Create branch (jn-1234-feature)
    Dev->>Agor: Start Setup Session

    Agor->>Git: Extract ticket from branch name
    Git-->>Agor: JN-1234

    Agor->>Jira: Fetch ticket details
    Jira-->>Agor: Ticket info + parent story

    Agor->>Agor: Store {worktree.issue_url}

    Agor->>GitHub: Check for existing PR
    GitHub-->>Agor: No PR found

    Agor->>GitHub: Create Draft PR
    GitHub-->>Agor: PR URL

    Agor->>Agor: Store {worktree.pull_request_url}

    Note over Agor: Setup Complete

    Dev->>Agor: Start Specify Session
    Agor->>Jira: Fetch full context
    Jira-->>Agor: Requirements + acceptance criteria
    Agor->>Agor: Generate specification doc

    Dev->>Agor: Start Clarify Session
    Agor->>Agor: Identify underspecified areas
    Agor->>Dev: Questions for clarification
    Dev-->>Agor: Answers

    Note over Dev,GitHub: Continue through Plan → Tasks → Analyze → Implement
```

---

## Viewing These Diagrams

These Mermaid diagrams render automatically in:

- **GitHub/GitLab**: Markdown preview in repositories
- **VS Code**: With Mermaid extension installed
- **Mermaid Live Editor**: [mermaid.live](https://mermaid.live)
- **Documentation tools**: Docusaurus, MkDocs, etc.

To test or modify diagrams, copy the code blocks to [mermaid.live](https://mermaid.live) for interactive editing.
