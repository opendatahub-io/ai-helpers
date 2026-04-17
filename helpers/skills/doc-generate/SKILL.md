---
name: doc-generate
description: >
  Generate AsciiDoc documentation modules from gathered context.
  Reads context package and gap report, generates content, then
  self-validates with iterative correction (up to 3 retries).
  Produces generated files and workspace/generation-report.json.
argument-hint: "[--type concept|procedure|reference|assembly] [--topic <topic>]"
model: claude-opus-4-6
effort: high
---

# doc-generate

Generate modular AsciiDoc documentation from gathered context, with built-in validation and iterative correction.

## Prerequisites

- `workspace/context-package.json` must exist (produced by `doc-gather`)
- `workspace/gap-report.json` should exist (produced by `doc-gap`); if missing, proceed with generation but note the absence

## Parse arguments

`$ARGUMENTS` optionally contains:
- `--type <type>`: restrict generation to a specific module type (concept, procedure, reference, assembly)
- `--topic <topic>`: focus generation on a specific topic within the feature

If no arguments, generate all appropriate module types based on the feature.

## Step 1: Read inputs

1. Read `workspace/context-package.json`
2. Read `workspace/gap-report.json` (if exists)
3. Read `${CLAUDE_SKILL_DIR}/prompts/generate-docs.md`
4. Source `${CLAUDE_SKILL_DIR}/scripts/product-config.sh` and `${CLAUDE_SKILL_DIR}/scripts/asciidoc-conventions.sh` for module templates

Check gap report recommendation:
- If `stop`: halt and report to caller that context is insufficient
- If `gather-more`: warn but proceed with available context
- If `proceed`: continue normally

## Step 2: Determine doc types needed

Based on the ticket metadata and context, determine which module types to generate:

- **New feature**: concept + procedure + reference (if API) + assembly
- **Behavior change**: update existing procedure or concept
- **API change**: reference module (or update existing)
- **Configuration change**: reference module with parameter table
- **Bug fix with user impact**: update existing procedure or add troubleshooting

If `--type` was specified, restrict to that type.

## Step 3: Generate documentation

Read the product conventions from the context package:
- Module prefixes (con_, proc_, ref_, assembly_, snip_)
- Documentation framework (asciidoc-modular)
- Attribute files
- Variants (upstream, self-managed)

For each module to generate:

1. Select relevant context files (highest relevance scores first)
2. Construct generation prompt combining:
   - `${CLAUDE_SKILL_DIR}/prompts/generate-docs.md` template
   - Ticket metadata
   - Selected context file contents
   - Gap analysis findings relevant to this module
   - Product conventions
3. Generate the AsciiDoc content via LLM
4. Apply module structure from `${CLAUDE_SKILL_DIR}/scripts/asciidoc-conventions.sh`

## Step 4: Self-validate (iteration loop)

For each generated module, run validation:

1. Write generated content to a temporary file
2. Run deterministic validation:
   ```bash
   bash ${CLAUDE_SKILL_DIR}/scripts/validate-artifacts.sh <temp-file>
   ```
3. Check structural requirements:
   - Module ID present
   - Content type attribute set
   - Heading present
   - Filename matches module type prefix

4. If validation finds issues:
   - Feed findings back to LLM with the generated content
   - Ask LLM to fix the specific issues
   - Re-validate
   - Repeat up to **3 iterations**

5. Track iteration count and findings per iteration

## Step 5: Write output files

Write generated modules to `workspace/generated-docs/`:

```
workspace/generated-docs/
├── con_feature-name.adoc
├── proc_feature-name.adoc
├── ref_feature-name-parameters.adoc
└── assembly_feature-name.adoc
```

## Step 6: Write generation report

Write `workspace/generation-report.json`:

```json
{
    "generated_at": "2026-04-14T10:45:00Z",
    "ticket_key": "RHOAIENG-55490",
    "gap_report_recommendation": "proceed",
    "modules": [
        {
            "filename": "con_feature-name.adoc",
            "type": "concept",
            "title": "Understanding feature name",
            "confidence": 0.85,
            "iterations": 1,
            "validation_status": "pass",
            "validation_findings_initial": 2,
            "validation_findings_final": 0,
            "context_sources_used": [
                "modules/existing/con_related.adoc",
                "api/types/feature_types.go"
            ],
            "notes": "SME review recommended for accuracy of step 3"
        }
    ],
    "assembly": {
        "filename": "assembly_feature-name.adoc",
        "includes": ["con_feature-name.adoc", "proc_feature-name.adoc"]
    },
    "summary": {
        "total_modules": 3,
        "average_confidence": 0.82,
        "total_iterations": 5,
        "modules_with_remaining_issues": 0
    }
}
```

## Output

Primary: Generated AsciiDoc files in `workspace/generated-docs/`
Secondary: `workspace/generation-report.json`
Report to caller: number of modules generated, average confidence, iteration summary.

## Stop conditions

- **Halt**: Gap report recommendation is `stop`
- **Halt**: Context package is empty (no context files)
- **Warn**: Gap report missing (proceed with caution)
- **Warn**: Validation issues remain after 3 iterations (write files anyway, note in report)
- **Continue**: Individual module generation fails (skip and note in report)
