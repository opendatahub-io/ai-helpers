---
name: doc-gap
description: >
  Analyze context sufficiency for documentation generation. Reads
  workspace/context-package.json and produces workspace/gap-report.json
  with severity-rated gaps and a proceed/gather-more/stop recommendation.
argument-hint: "[component-focus]"
model: claude-sonnet-4-5
effort: medium
---

# doc-gap

Assess whether the gathered context is sufficient to produce quality documentation.

## Prerequisites

`workspace/context-package.json` must exist (produced by `doc-gather`).

## Parse arguments

`$ARGUMENTS` optionally contains a component name to focus the analysis on. If empty, analyze all components found in the context package.

## Step 1: Read context package

Read `workspace/context-package.json` and extract:
- Ticket metadata (summary, components, fix_versions)
- List of gathered context files with their source types
- Product configuration (docs conventions)

## Step 2: Deterministic coverage checks

Perform these checks without LLM judgment:

1. **Component coverage**: For each component in the ticket, check if at least one context file from that component's repo exists.
2. **Documentation existence**: Check if existing documentation files are present in the context.
3. **API reference availability**: If the ticket involves API changes, check for CRD type definitions or API spec files.
4. **Source code presence**: Check if implementation source code is included.
5. **Architecture docs**: Check for architecture context files.

Record each check as a finding with pass/fail status.

## Step 3: LLM assessment

Read the gap analysis prompt from `${CLAUDE_SKILL_DIR}/prompts/gap-analysis.md`.

Construct an LLM prompt combining:
- The gap analysis prompt template
- Ticket metadata from the context package
- Summary of gathered files (file paths, source types, relevance scores)
- Content snippets from the highest-scored files (first 500 chars each, up to 20 files)
- Results of deterministic checks from Step 2

Ask the LLM to assess:
- Is the context sufficient to write accurate docs?
- What specific information is missing?
- What is the recommendation: proceed, gather-more, or stop?

## Step 4: Synthesize findings

Combine deterministic check results with LLM assessment into a unified gap report.

## Step 5: Write gap report

Write `workspace/gap-report.json` with this structure:

```json
{
    "recommendation": "proceed",
    "confidence": 0.82,
    "summary": "Context is sufficient for basic documentation...",
    "deterministic_checks": [
        {
            "check": "component_coverage",
            "status": "pass",
            "details": "Found context for 2/2 ticket components"
        }
    ],
    "gaps": [
        {
            "severity": "medium",
            "category": "examples",
            "description": "No sample YAML configurations found",
            "impact": "Documentation will lack concrete examples",
            "suggestion": "Check component repo for example/ directory"
        }
    ],
    "existing_coverage": [
        {
            "topic": "Model serving overview",
            "source": "modules/serving/pages/con_model-serving.adoc",
            "quality": "sufficient"
        }
    ],
    "analyzed_at": "2026-04-14T10:35:00Z"
}
```

## Output

Primary: `workspace/gap-report.json`
Report to caller: recommendation, confidence score, number of gaps by severity.
