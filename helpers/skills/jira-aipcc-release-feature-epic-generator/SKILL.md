---
name: jira-aipcc-release-feature-epic-generator
description: |
  Generate JIRA features and epics for an AIPCC release from the accelerator
  variant planning spreadsheet. Use when creating release work items, generating
  feature/epic lists for a new release version, or preparing JIRA templates.
  Triggers: "generate features for release", "create release features",
  "release feature list", "JIRA template for release".
allowed-tools: Bash, AskUserQuestion, Read, Write
argument-hint: "<release-version>"
metadata:
  author: AIPCC Development Platform
  tags: [jira, release, aipcc, planning]
---

# Generate Release Features

Create a complete set of JIRA Features, Epics, Stories, and Tasks for an AIPCC release by reading version data from the accelerator variant planning spreadsheet and applying it to the variant configuration template.

**Paths:** All asset paths in this skill resolve from the skill base directory shown in the skill loading output.

## Prerequisites

Verify before starting:

- `gws` CLI available: `which gws`
- Google Sheets access authenticated (the spreadsheet requires auth)
- `acli` CLI available and authenticated: `acli jira auth status`

## Input

**Release version:** `$ARGUMENTS` should contain the release version (e.g., `3.5-EA2`, `3.6-EA1`).

If no version is provided, ask the user for the target release version.

**Spreadsheet URL:** Always ask the user for the Google Spreadsheet URL. The URL may change between releases. Extract the spreadsheet ID (the 44-character alphanumeric token) from the URL — it appears after `/d/` and before the next `/` or query parameter (e.g., `?usp=sharing`). Handle URL variants like `/spreadsheets/u/0/d/<ID>/`.

## Workflow

### Step 1: Setup

1. Sanitize the version for use as a directory name: strip all characters except alphanumerics, dots, and underscores (e.g., `3.5-EA2` → `3.5EA2`). Reject the input if the result is empty or starts with `.`.
2. Create the output directory: `ep-working-docs/<sanitized-version>/`
3. Load the variant configuration from `<skill-base>/assets/variant-config.yaml`
4. Extract the spreadsheet ID from the user-provided URL

### Step 2: Discover Sheets

Read the spreadsheet metadata to list all sheet names:

```bash
gws sheets spreadsheets get --params '{"spreadsheetId": "<ID>"}'
```

Parse the JSON response to extract sheet titles and IDs. Filter out non-accelerator sheets:
- Skip sheets named "Retired*", "Major related releases", "Additional info", or similar metadata sheets
- Keep sheets that match the `sheet` field in any `accelerator_sheets` entry from the variant config

If a sheet in the spreadsheet doesn't match any config entry, note it as unrecognized and report it at the end.

### Step 3: Read All Sheets and Identify Version Tracks

For each accelerator sheet, read ALL rows (up to 50 rows) to capture all version track sections:

```bash
gws sheets spreadsheets values get --params '{"spreadsheetId": "<ID>", "range": "<sheet-name>!A1:Z50"}'
```

Note: If a sheet name contains special characters (spaces, apostrophes), ensure proper JSON escaping in the `range` value.

Parse the JSON `values` array. Each row is an array of cell values.

**Identify the release header row:** Row index 1 (0-indexed) contains `"Release:"` in column 0, followed by release version names. Find the column index of the target release version. Match flexibly — the spreadsheet may use variations:
- `"RHAI 3.5 EA2"` or `"RHAI 3.5-EA2"` or `"RHAI 3.5. EA2"`
- Strip whitespace and normalize when comparing

**Identify version track sections:** Scan rows looking for track headers. A track header row has a non-empty value in column A that matches the `track_pattern` from the variant config for this sheet. Examples:
- On the CUDA sheet: `"CUDA 12.9"`, `"CUDA 13.0"`, `"CUDA 13.2"`
- On the ROCm sheet: `"ROCm 6.4"`, `"ROCm 7.1"`, `"ROCm 7.13"`, `"ROCm 7.2"`

Each track section extends from its header row until the next blank row or the next track header.

**Important:** Check for special markers that indicate a track is not for general release:
- `"INTERNAL ONLY"` in any cell — skip this track
- `"No Future Releases"` in the target column — mark as discontinued

### Step 4: Filter Active Tracks

For each version track identified in Step 3:

1. Check if the track has data in the target release column (column index found in the release header)
2. A track is **active** if its header row has a non-empty value in the target column
3. A track is **discontinued** if the target column contains text like "No Future Releases" or is explicitly marked as ended
4. A track is **not applicable** if its data doesn't extend to the target column (row is shorter)

Only active tracks become Features. Record the reason for excluding each inactive track.

### Step 5: Extract Version Data

For each active track, scan its rows and extract version data from the target release column:

| Data Point | How to Find |
|------------|-------------|
| Accelerator version | Track header row, target column (e.g., "CUDA 12.9", "ROCm 7.2.x") |
| Python | Row where column A contains "python" (case-insensitive) |
| Torch | Row where column A contains "torch" (case-insensitive) |
| vLLM | Row where column A contains "vllm" (case-insensitive) |
| Extra versions | Match `extra_version_rows` patterns from variant config against column A |

**Handling version values:**
- If the cell contains `(?)` or `?`, keep the value but mark it as tentative: `"2.11 (?)"` → `"2.11 (?)"`
- If the row exists but the target column cell is empty or missing, record as `"TBD"`
- If the entire row doesn't exist for this track, record as `"TBD"`
- Strip the package name prefix: `"torch 2.10"` → `"2.10"`, `"vllm 0.19.1"` → `"0.19.1"`
- Preserve slash alternatives: `"torch 2.10/2.11(?)"` → `"2.10/2.11 (?)"`

### Step 6: Map Tracks to Variants

For each active track, construct the variant name:

1. Look up the sheet's config entry in `accelerator_sheets`
2. If `variant_name_override` is set, use it as the base name (e.g., `"gaudi"`, `"cpu"`, `"tpu"`)
3. Otherwise, derive the name from the track header:
   - Extract the version number from the track name (e.g., `"CUDA 12.9"` → `"12.9"`, `"ROCm 7.2"` → `"7.2"`)
   - Combine: `{accelerator}{version}` (e.g., `"cuda12.9"`, `"rocm7.2"`)
4. Append `variant_suffix` (always `"-ubi9"` currently): `"cuda12.9-ubi9"`, `"rocm7.2-ubi9"`

**Select the epic template:**
- If the sheet config has a simple `epic_template` field, use that template for all tracks
- If it has `epic_template_rules`, evaluate each rule's `match` against the track's version number. Use the first matching rule's template. Fall back to `default` if no rule matches.

**Handle new/unknown variants:**
If a track doesn't match any expected pattern, flag it as **(NEW)** in the output and use the closest matching epic template. Note it in the version summary for the user to review.

### Step 7: Generate Outputs

Produce three files in the output directory:

#### 7a. `versions.md` — Version Summary

Structure:
```markdown
# RHAI <version> — Accelerator Version Matrix

Extracted from [spreadsheet](URL) on <date>.

## Version Matrix
| Variant | Python | Torch | vLLM | Accelerator-Specific Version |
...

## Additional Packages
(If any variant has extra packages beyond python/torch/vllm)

## Variant Selection Rationale
| Sheet | Tracks in sheet | Included | Excluded (with reason) |
...

## Notes
- List any tentative values, missing data, discontinued tracks, new variants
```

#### 7b. `<version>-jira-template.yaml` — JIRA Template

Structure:
```yaml
release:
  version: "<version>"
  products: [from jira_defaults]
  project: <from jira_defaults>
  components: [from jira_defaults]

variants:
  - name: <variant-name>
    labels: [from squad config]
    versions:
      python: "<value>"
      torch: "<value>"
      vllm: "<value>"
      # ... additional per-variant
    template:
      - type: Feature
        summary: "<variant> for <version>"
        description: "..."
        assignee: "<from squad config>"
        watchers: [from squad config]
        children:
          - type: Epic
            summary: "<resolved from epic template>"
            description: "..."
          # ... more epics

squads:
  # Cross-cutting squads from variant config, with {version} resolved
```

**Resolving placeholders in epic templates:**
- `{variant}` → variant name (e.g., `"cuda12.9-ubi9"`)
- `{version}` → release version (e.g., `"3.5-EA2"`)
- `{torch}` → torch version from spreadsheet (e.g., `"2.10 (?)"`)
- `{vllm}` → vLLM version from spreadsheet
- `{accel_version}` → accelerator-specific version (e.g., `"Gaudi 1.24"`)
- `{accelerator}` → accelerator display name (e.g., `"CUDA"`, `"ROCm 7.2"`)

If a placeholder value is `"TBD"`, keep it as-is in the summary (e.g., `"Update torch to TBD"`). Add a description noting the value is not yet in the spreadsheet.

#### 7c. `features-epics.md` — Human-Readable Listing

Structure:
```markdown
# RHAI <version> — Features & Epics

Generated from ... on <date>.

(Explanation of (?) and TBD markers)

---

## 1. <variant-name>

**Squad:** <name> | **Lead:** <lead> (`<assignee>`)
(**Watchers:** <list>, if any)

| # | Type | Summary | Status |
|---|------|---------|--------|
| 1 | Feature | <variant> for <version> | |
| 1.1 | Epic | <epic summary> | <notes if tentative/TBD> |
...

---
(repeat for each variant, numbered sequentially)

## N. Base Images Squad
## N+1. Delivery Squad

---

## Summary
| | Features | Epics | Stories | Tasks | Total |
...

### Changes from base template
(List any new variants, removed variants, or renamed variants vs the config)
```

**Numbering:** Variants are numbered sequentially starting at 1. Cross-cutting squads continue the sequence. Within each variant, children are numbered hierarchically (1.1, 1.2, 7.2.1, etc.).

### Step 8: Report

After generating all files, report to the user:

1. Files created (with paths)
2. Number of Features, Epics, Stories, Tasks generated
3. Any variants flagged as NEW (not in config)
4. Any tentative or missing version data that needs squad lead confirmation
5. Any discontinued or excluded tracks

## JIRA Ticket Creation

After generating the output files, the user may ask to create the actual JIRA tickets. This phase uses the JIRA creation config at `<skill-base>/assets/jira-creation-config.yaml`.

### Required Prompts

Before creating any tickets, **always** perform these steps:

1. **Read the release schedule spreadsheet** — The URL is in `jira-creation-config.yaml` under `schedule_spreadsheet`. Extract the spreadsheet ID and read all rows. Find the section matching the target release (e.g., "RH AI 3.5 EA2" as a row header). Extract key milestone dates from that section. Dates in the spreadsheet may lack a year — resolve using this precedence: (1) extract year from the release version string if present, (2) use surrounding dates in the schedule that do include a year, (3) current year as final fallback. Flag any inferred years for explicit user confirmation. Present a table of key milestones to the user.

2. **Resolve due dates from milestones** — Use the milestone names in `jira-creation-config.yaml` to look up dates:
   - `due_dates.feature_milestone` → Feature due date (default: "AIPCC Code Freeze")
   - `due_dates.epic_milestone` → default Epic due date (default: end date of "AIPCC Base Image Development" range)
   - `epic_due_date_overrides` → per-epic overrides where specific epics use a different milestone. Match epic summaries against the override keys (keys may contain `{version}` placeholders). Apply the override milestone date instead of the default.

   Present the resolved dates to the user for confirmation before proceeding.

3. **Review the JIRA creation config** — Confirm or update: component, label, team, fix version, default assignee, parent issue. Show current values and ask if any need changing.

### Creation Workflow

Process **one variant at a time**. For each variant:

1. Present the Feature and its child Epics to the user for confirmation
2. Wait for user approval before creating
3. Create the Feature issue first (captures the returned issue key)
4. Create each child Epic with `parent` set to the Feature key
5. Create any child Stories/Tasks with `parent` set to their Epic key
6. Report the created issue keys

### Issue JSON Template

Use `acli jira workitem create --from-json <file>` with this structure:

```json
{
  "projectKey": "<project>",
  "type": "<Feature|Epic|Story|Task>",
  "summary": "<from release template>",
  "description": {
    "version": 1,
    "type": "doc",
    "content": [
      {
        "type": "paragraph",
        "content": [
          {"type": "text", "text": "<description text>"}
        ]
      }
    ]
  },
  "additionalAttributes": {
    "components": [{"name": "<component>"}],
    "labels": ["<label>"],
    "duedate": "<YYYY-MM-DD>",
    "fixVersions": [{"name": "<fix_version>"}],
    "customfield_10855": [{"name": "<target_version>"}],
    "parent": {"key": "<parent-key>"}
  }
}
```

**Field mapping by issue type:**

| Field | Feature | Epic | Story/Task |
|-------|---------|------|------------|
| `duedate` | From `feature_milestone` | From `epic_milestone` (or `epic_due_date_overrides` if epic summary matches) | Inherit parent Epic's due date |
| `parent` | From config (or omit) | Feature key | Epic key |
| `labels` | From JIRA creation config | From JIRA creation config | From JIRA creation config |
| `customfield_10855` | Target Version from config | Target Version from config | Target Version from config |

### Team Field

The Team field (`customfield_10001`) may not be settable via API due to Jira screen restrictions. Attempt to set it via `additionalAttributes`; if creation fails, retry without it and inform the user to set it manually on the board.

## Output Reference

Example output from a successful run for RHAI 3.5 EA2 is available at:
- `ep-working-docs/3.5EA2/versions.md`
- `ep-working-docs/3.5EA2/3.5-EA2-jira-template.yaml`
- `ep-working-docs/3.5EA2/features-epics.md`

Use these as reference for output format and content expectations.
