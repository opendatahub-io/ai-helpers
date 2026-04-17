---
name: doc-review
description: >
  Adversarial review of AsciiDoc documentation against context sources.
  Checks factual accuracy, completeness, consistency, and hallucination.
  Produces workspace/review-findings.json.
argument-hint: "<file-or-directory> [--context workspace/context-package.json]"
model: claude-opus-4-6
effort: high
---

# doc-review

Perform adversarial comparison of documentation content against context sources to detect inaccuracies, omissions, and hallucinations.

## Prerequisites

- AsciiDoc files to review (specified in arguments)
- `workspace/context-package.json` should exist for cross-reference checking

## Parse arguments

`$ARGUMENTS` contains:
1. **Target**: file path, directory, or glob pattern for AsciiDoc files to review
2. **--context** (optional): path to context package (defaults to `workspace/context-package.json`)

## Step 1: Discover files

Resolve the target to a list of `.adoc` files:
- Single file: review that file
- Directory: glob `**/*.adoc`
- Glob pattern: expand it

## Step 2: Load context

Read `workspace/context-package.json` and extract:
- Ticket metadata (summary, description, components)
- Context files with content (source code, API specs, architecture docs, existing docs)
- Product conventions

Group context files by type for targeted comparison:
- **Source code**: `.go`, `.py`, `.java` files — authoritative for API behavior
- **API specs**: `*_types.go`, `*.yaml` CRD files — authoritative for field names and schemas
- **Architecture docs**: `.md` files from architecture repos — authoritative for design
- **Existing docs**: `.adoc` files — reference for style and terminology

## Step 3: Review each file

For each AsciiDoc file, read its content and construct a review prompt combining:

1. Read `${CLAUDE_SKILL_DIR}/prompts/review-content.md` template
2. The documentation content being reviewed
3. Relevant context files (matched by topic/component)
4. Ticket metadata

Ask the LLM to perform adversarial review:

- **Factual accuracy**: Compare every technical claim against source code and API specs
- **Completeness**: Check if important details from the ticket and context are covered
- **Consistency**: Verify terminology matches existing documentation
- **Hallucination check**: Flag any API fields, CLI flags, config options, or behaviors not found in context sources

## Step 4: Compile findings

Merge findings from all reviewed files:

```json
{
    "reviewed_at": "2026-04-14T10:50:00Z",
    "files_reviewed": 3,
    "confidence": 0.78,
    "summary": "Documentation is largely accurate but has 2 technical issues...",
    "findings": [
        {
            "category": "technical_inaccuracy",
            "severity": "high",
            "description": "The documented API field 'replicas' should be 'minReplicas'",
            "file_path": "modules/serving/pages/ref_model-serving-params.adoc",
            "line_start": 42,
            "line_end": 42,
            "context_source": "api/v1alpha1/servingruntime_types.go:87",
            "suggestion": "Change 'replicas' to 'minReplicas' per the CRD type definition"
        }
    ],
    "summary_by_severity": {
        "high": 1,
        "medium": 2,
        "low": 3,
        "total": 6
    }
}
```

## Step 5: Write findings

Write `workspace/review-findings.json`.

## Output

Primary: `workspace/review-findings.json`
Report to caller: confidence score, total findings by severity, files reviewed.

## Stop conditions

- **Halt**: No files found matching target
- **Warn and continue**: Context package missing (review without cross-reference)
- **Continue**: Individual file review fails (record error, continue with others)
