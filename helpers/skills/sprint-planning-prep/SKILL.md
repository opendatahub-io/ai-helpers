---
name: sprint-planning-prep
description: Automate Monday sprint planning preparation for AIPCC Ecosystems team (8 squads)
allowed-tools: mcp__atlassian__*
user-invocable: true
---

# Sprint Planning Prep

Automates the 30-45 minute Monday sprint planning preparation by pulling Jira data from the AIPCC project, analyzing priorities across 8 Ecosystems squads, and generating a formatted planning document.

## Prerequisites

- Atlassian MCP server configured and authenticated
- Access to AIPCC Jira project
- Configuration file at `~/.claude/sprint-planning-config.json`

## Configuration

Create `~/.claude/sprint-planning-config.json`:

```json
{
  "version": "1.0",
  "team_mapping": {
    "198313f9-60da-45f1-9b00-ec528c14d86f": "CUDA",
    "35460972-bc42-49e4-a321-d96d103e14e1": "AWS Neuron",
    "780dbb59-633d-4b10-9460-eb77676fca68": "ROCm",
    "f36d29d9-69a0-4ad7-86cd-21f78f6553fa": "IBM Spyre",
    "6b546077-219c-4d9a-90e6-e139c52e20e5": "TPU",
    "2bb893ee-a908-4cce-8e19-281cec70a1ad": "Gaudi",
    "8700a5e5-b786-42cf-b48e-c9cc6a8ba622": "Delivery",
    "cbfda236-8194-4aef-8aa9-379741ce5587": "Tooling"
  },
  "jira_cloud_id": "2b9e35e3-6bd3-4cec-b838-f4249ee02432",
  "jira_project": "AIPCC",
  "components": [
    "Accelerator Enablement",
    "AIPCC Ecosystems",
    "Development Platform",
    "Wheel Package Index"
  ]
}
```

## Usage

Simply invoke the skill:

```
run sprint planning prep
```

Or specify a target Monday date:

```
run sprint planning prep for 2026-06-08
```

## Implementation

This skill performs the following steps:

1. **Determine sprint dates and fix version**
   - Calculate next Monday's date (or use provided date)
   - Identify the current fix version for sprint planning (e.g., rhoai-3.5.EA2)

2. **Query Jira data**
   - Search for all Features, Initiatives, Epics, and Stories in AIPCC project
   - Filter by target fix version and configured components
   - Pull epic details, parent features, assignees, and status

3. **Analyze by squad**
   - Group work items by the 8 accelerator squads using team field mapping
   - Count epics by status (Closed, In Progress, New, To Do)
   - Identify unassigned work

4. **Generate contextual questions**
   - Analyze patterns (old work, capacity warnings, blockers)
   - Create squad-specific questions for Monday planning call
   - Flag risks and code freeze readiness

5. **Create planning document**
   - Generate markdown with executive summary
   - Squad-by-squad breakdown with clickable Jira links
   - Nested bullet lists for epic organization
   - Cross-squad analysis and recommendations
   - Save to `~/sprint-planning-YYYY-MM-DD.md`

## Output Format

The generated markdown includes:

### Executive Summary
- Total epic count for current fix version
- Status breakdown (Closed/In Progress/New/To Do)
- Code freeze alerts
- Risk assessment

### Squad-by-Squad Breakdown

For each of 8 squads (CUDA, ROCm, Gaudi, IBM Spyre, TPU, AWS Neuron, Delivery, Tooling):
- Epic count by status
- Clickable links to all epics (grouped by status)
- Parent features tracked
- Contextual questions based on patterns

### Cross-Squad Analysis
- Positive indicators
- Risk flags
- Recommendations
- Code freeze readiness

## Converting to Google Doc

To create a polished Google Doc from the generated markdown:

1. Set up Google Docs API (one-time, see `/Users/belwell/GOOGLE-DOCS-SETUP.md`)
2. Run the conversion script:

```bash
source ~/google-docs-env/bin/activate
python3 ~/create-google-doc-final.py ~/sprint-planning-YYYY-MM-DD.md
```

This creates a professionally formatted Google Doc with:
- Proper heading hierarchy
- Nested bullets for epic lists
- Clickable Jira links
- Professional spacing

## Example Workflow

**Sunday evening or Monday morning:**

1. Generate sprint planning analysis:
   ```
   run sprint planning prep
   ```

2. Convert to Google Doc:
   ```bash
   source ~/google-docs-env/bin/activate
   python3 ~/create-google-doc-final.py ~/sprint-planning-2026-06-08.md
   ```

3. Share Google Doc link with squad leads 30+ minutes before Monday call

4. Use during Monday call to walk through each squad's priorities (6-8 min per squad)

## Squads

- **IBM Spyre** - IBM Power systems acceleration
- **CUDA** - NVIDIA GPU enablement
- **TPU** - Google TPU support
- **ROCm** - AMD GPU acceleration
- **Gaudi** - Intel Gaudi accelerator
- **AWS Neuron** - AWS inferentia/trainium
- **Delivery** - Release and packaging
- **Tooling** - Development tools and infrastructure

## Components

- Accelerator Enablement
- AIPCC Ecosystems
- Development Platform
- Wheel Package Index

## Error Handling

The skill handles:
- Missing configuration file (prompts to create one)
- Atlassian MCP authentication failures (guides through OAuth)
- Empty sprint data (notifies and suggests fix version check)
- Unassigned epics (creates "Unassigned Work" section)

## Related Documentation

- Full README: `~/.claude/skills/sprint-planning-prep/README.md`
- Google Docs setup: `/Users/belwell/GOOGLE-DOCS-SETUP.md`
- Process design: `/Users/belwell/docs/superpowers/specs/2026-05-29-ecosystems-sprint-planning-design.md`
- Skill design: `/Users/belwell/docs/superpowers/specs/2026-06-05-sprint-planning-skill-design.md`
