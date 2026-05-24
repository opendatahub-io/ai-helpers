---
name: conforma-doc-search
description: Look up troubleshooting documentation for a Conforma violation by its violation code. Performs deterministic YAML file lookup with pattern-based fallback. Use when investigating a Conforma violation and needing known root causes, fix steps, or exception guidance.
allowed-tools: Bash(python3:*)
---

# Conforma Doc Search

Deterministic lookup of per-violation YAML documentation files by violation code. Zero LLM tokens -- this is a file read, not a search.

## How It Works

1. Takes a `violation_code` from the handover's `investigation.violation`
2. Reads `references/violations/{violation_code}.yaml` -- direct file read
3. If no exact file match: searches `patterns` fields across all YAML files for the violation's `msg` text (fallback)
4. Returns the parsed YAML content as structured data in the handover

## Instructions

```bash
python3 scripts/search_docs.py --handover <handover.json> [--output <output.json>]
```

### Arguments

- `--handover` (required): path to handover JSON with `investigation.violation` populated
- `--output` (optional): path to write the updated handover JSON (default: stdout)

### Output

Updates the handover `investigation.doc_search` section with:
- `violation_file`: path to the matched YAML file
- `violation_data`: parsed YAML content (violation_code, rule, patterns, symptoms, root_cause, fix_steps, exception_guidance, resolved_cases)
- `related_files`: paths to related violation YAML files (e.g., same rule prefix)
- `match_type`: `"exact"`, `"pattern"`, or `"none"`

### Reference Documents

- `references/conforma-policy-reference.md` -- curated upstream conforma.dev docs (static)
- `references/violations/*.yaml` -- per-violation YAML files (self-improving via `conforma-doc-update`)
- `references/external-references.yaml` -- upstream URLs to fetch at runtime (shared across skills/agents)

## Error Handling

- If no violation file matches and pattern fallback finds nothing, set `match_type` to `"none"` (not an error -- the violation is simply undocumented)
- If `investigation.violation` is missing, exit with a prerequisite error
