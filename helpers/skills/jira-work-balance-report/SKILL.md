---
name: jira-work-balance-report
description: Analyze a Jira Plan CSV export to measure work distribution against org targets (40% Tech Debt, 40% New Features, 20% Learning). Use when user wants to understand work balance, portfolio distribution, or alignment with organizational goals.
allowed-tools: Bash
user-invocable: true
argument-hint: "<path-to-csv> [--hierarchy Epic,Feature] [--team TeamName]"
---

# Work Balance Report

Analyze a Jira Plan CSV export to measure how work is distributed across organizational investment categories and whether the balance aligns with targets.

## Org Targets

- **40% Tech Debt & Quality**: Bug fixing, test coverage, stability, security, packaging, backports
- **40% New Features**: New feature development, RFEs, enhancements
- **20% Learning & Enablement**: Training, spikes, AI research, enablement, onboarding

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- A CSV file exported from a Jira Plan (e.g., from https://redhat.atlassian.net/jira/plans/)
- Optionally: `JIRA_API_TOKEN` and `JIRA_EMAIL` for jira-activity deep dives

## Usage

This skill reads a Jira Plan CSV, classifies work items, and produces a report comparing actual distribution against the 40/40/20 target.

The CSV is assumed to be ordered from highest to lowest priority (as exported from Jira Plans). This ordering is used to analyze whether high-priority work aligns with org investment goals.

## Implementation

### Step 1: Determine the CSV File Path

1. If a file path is provided in the arguments, use it
2. Otherwise, search the conversation history for references to CSV files or Jira Plan exports
3. If no path is found, ask the user: "Which CSV file should I analyze? Please provide the path to your Jira Plan export."
4. Verify the file exists before proceeding

Optionally the user may specify:
- `--hierarchy Epic,Feature` to filter to specific hierarchy levels
- `--team "Team Name"` to filter to a specific team

### Step 2: Run the Analysis Script

Run the analysis script located at `scripts/analyze_plan_balance.py` relative to this skill. Execute it directly (not via `python`) to invoke uv via the shebang:

```bash
./scripts/analyze_plan_balance.py <csv-file> [--hierarchy Epic,Feature] [--team "Team Name"]
```

The script outputs JSON to stdout containing:
- Classified items with category, confidence, and reasoning
- Distribution summaries (all items, active items only, by priority band, by team)
- Items with low classification confidence flagged for review
- Comparison against org targets with deltas

### Step 3: Review Low-Confidence Classifications

Examine the `low_confidence_items` array in the output. These items were classified as "New Features" by default because no strong signal was detected. For each low-confidence item:

1. Read the title and any labels carefully
2. Determine if the item actually belongs to a different category:
   - Work related to bugs, tests, CI, builds, packaging, security, compliance, backports, errata → **Tech Debt & Quality**
   - Work related to spikes, research, training, onboarding, experimentation, AI adoption → **Learning & Enablement**
   - Work related to new capabilities, features, enhancements, integrations → **New Features**
3. Mentally adjust the distribution numbers based on your reclassifications

This is where your judgment adds the most value — the script handles clear cases, you handle the ambiguous ones.

### Step 4: Optionally Deep-Dive with jira-activity

If the user wants to understand actual engineering effort (not just planned work), suggest running the `jira-activity` skill on specific high-priority tickets. This reveals:
- Whether engineers are actively working on the planned items
- If effort is going to items not in the plan
- Staleness patterns that indicate misalignment

Do NOT run jira-activity automatically — suggest it as an optional next step for tickets of interest.

### Step 5: Generate the Report

Produce a structured report with these sections:

#### Overall Work Balance

Present the distribution as a table comparing actual vs target:

| Category | Count | Actual % | Target % | Delta |
|----------|-------|----------|----------|-------|
| Tech Debt & Quality | N | X% | 40% | +/-Y% |
| New Features | N | X% | 40% | +/-Y% |
| Learning & Enablement | N | X% | 20% | +/-Y% |

If estimate data is available, include an estimate-weighted column as well.

Call out whether the org is over/under-investing in each category relative to targets.

#### Active Work Distribution

Same table but filtered to items with status "In Progress" or "Review". This shows what engineers are actually working on right now vs what is planned.

#### Priority Band Analysis

The CSV rows are ordered by priority. Break items into quartiles:
- **Top quartile**: Highest priority items — what category do they fall into?
- **Bottom quartile**: Lowest priority items — is there a pattern?

Highlight if high-priority work skews heavily toward one category (e.g., top quartile is 80% new features, meaning tech debt gets deprioritized).

#### Team Breakdown

Show distribution per team. Flag teams that are significantly out of balance compared to org targets.

#### Classification Confidence

Report how many items were classified with high, medium, and low confidence. List the reclassifications you made in Step 3 and the adjusted numbers.

#### Key Findings and Recommendations

Summarize:
- Is the org hitting the 40/40/20 target?
- Which category is most over/under-represented?
- Are high-priority items aligned with org goals?
- Per-team balance concerns
- Suggested rebalancing actions

## Error Handling

- **CSV Not Found**: Ask the user for the correct path
- **Empty CSV**: Report that no data was found
- **Missing Columns**: The script handles missing columns gracefully; report which columns were unavailable
- **No Items After Filtering**: Inform the user that filters excluded all items and suggest broader criteria

## Examples

### Basic Usage
```text
User: Analyze work balance from ~/Downloads/portfolio.csv
Assistant: [Runs script, reviews classifications, produces balance report]
```

### Team-Specific Analysis
```text
User: How is Frank's Team distributed against our 40/40/20 targets?
Assistant: [Runs script with --team "Frank's Team", produces team-specific report]
```

### Filtered by Hierarchy
```text
User: Show me the work balance for Epics only
Assistant: [Runs script with --hierarchy Epic, produces Epic-level report]
```

### With Deep Dive
```text
User: The top priority initiative looks stale, can you check?
Assistant: [Suggests running jira-activity on the specific ticket key]
```
