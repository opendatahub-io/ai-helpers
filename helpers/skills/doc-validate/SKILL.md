---
name: doc-validate
description: >
  Validate AsciiDoc documentation for technical accuracy using
  Extract-Identify-Validate pattern. Runs Vale, asciidoctor, lychee,
  YAML syntax checks, and LLM-powered cross-reference validation.
  Produces workspace/validation-findings.json.
argument-hint: "<file-or-directory> [--context workspace/context-package.json]"
model: claude-sonnet-4-5
effort: high
---

# doc-validate

Validate AsciiDoc documentation files for technical accuracy, style compliance, and structural correctness.

## Parse arguments

`$ARGUMENTS` contains:
1. **Target**: file path, directory, or glob pattern for AsciiDoc files to validate
2. **--context** (optional): path to context package for cross-reference validation (defaults to `workspace/context-package.json`)

## Step 1: Discover files

Resolve the target argument to a list of `.adoc` files:
- If a single file: validate that file
- If a directory: glob for `**/*.adoc`
- If a glob pattern: expand it

## Step 2: Run deterministic validators

Execute the validation script on all discovered files:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/validate-artifacts.sh <file1.adoc> <file2.adoc> ...
```

This runs:
- **Vale**: prose style compliance
- **Asciidoctor**: compilation check (can the file be built?)
- **Lychee**: link checking (are URLs valid?)
- **YAML syntax**: validate embedded YAML code blocks

Collect all findings from the script output.

## Step 3: Extract embedded artifacts

For each AsciiDoc file, extract embedded technical artifacts:

1. **YAML blocks**: Content within `[source,yaml]` delimiters
2. **CLI commands**: Content within `[source,bash]` or `[source,terminal]` delimiters
3. **Configuration references**: Attribute references like `{attribute-name}`
4. **API paths**: URLs or paths in the format `/api/v1/...`
5. **CRD references**: Kubernetes resource kinds and API versions

## Step 4: Cross-reference validation (LLM)

If a context package is available, use LLM judgment to cross-reference extracted artifacts against the gathered context:

For each extracted artifact:
- **YAML blocks**: Compare against CRD schemas and config examples in context
- **CLI commands**: Verify flags and options against --help output or source code in context
- **API paths**: Check against API specs or route definitions in context
- **CRD references**: Verify kind names, API versions, and field names against type definitions

Ask the LLM:
- Does this artifact match the authoritative source in the context?
- Are there incorrect field names, wrong API versions, or invalid options?
- Is the example complete and would it work as shown?

## Step 5: Structural validation

Check AsciiDoc structure requirements:

```bash
source ${CLAUDE_SKILL_DIR}/scripts/product-config.sh
source ${CLAUDE_SKILL_DIR}/scripts/asciidoc-conventions.sh
for file in <files>; do
    adoc_validate_structure "$file"
done
```

Verify:
- Module ID present (`[id="..."]`)
- Content type attribute set (`:_mod-docs-content-type:`)
- Level-1 heading present
- Module type matches filename prefix

## Step 6: Compile findings

Merge all findings from Steps 2-5, deduplicating and normalizing:

```json
{
    "validated_at": "2026-04-14T10:40:00Z",
    "files_validated": 5,
    "findings": [
        {
            "file": "modules/serving/pages/con_model-serving.adoc",
            "line": 42,
            "severity": "high|medium|low",
            "category": "vale|asciidoctor|lychee|yaml_syntax|cross_reference|structure",
            "tool": "vale|asciidoctor|lychee|yaml_syntax|llm|structural",
            "rule": "RedHat.Spelling",
            "message": "Description of the issue",
            "suggestion": "How to fix it"
        }
    ],
    "summary": {
        "high": 0,
        "medium": 3,
        "low": 5,
        "total": 8,
        "tools_run": ["vale", "asciidoctor", "yaml_syntax"],
        "tools_skipped": ["lychee"]
    }
}
```

## Step 7: Write findings

Write `workspace/validation-findings.json` with the compiled results.

## Output

Primary: `workspace/validation-findings.json`
Report to caller: total findings by severity, which tools ran vs skipped.

## Stop conditions

- **Continue**: Individual tool missing (warn and skip)
- **Continue**: Individual file fails to parse (record finding, continue)
- **Halt**: No files found matching the target argument
