---
name: aipcc-ecosystems-sprint-planning
description: Automate Monday sprint planning preparation for AIPCC Ecosystems team (8 squads)
allowed-tools: Bash
user-invocable: true
---

# AIPCC Ecosystems Sprint Planning

Automates the 30-45 minute Monday sprint planning preparation by pulling Jira data from the AIPCC project, analyzing priorities across 8 Ecosystems squads, and generating a formatted planning document.

## Prerequisites

- Python 3 and `uv` must be installed and available in PATH
- `JIRA_API_TOKEN` environment variable must be set with a valid API token for https://redhat.atlassian.net
- `JIRA_EMAIL` environment variable must be set with the email address associated with your Atlassian account
- Access to AIPCC Jira project with appropriate permissions
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

```text
run aipcc ecosystems sprint planning
```

Or specify a target Monday date:

```text
run aipcc ecosystems sprint planning for 2026-06-08
```

## Implementation

### Step 1: Determine Sprint Details

1. If the user provides a Monday date, use it
2. Otherwise, calculate the next Monday from today
3. Determine the fix version to analyze (e.g., rhoai-3.5.EA2)
   - If user specifies "for rhoai-3.5.EA3", use that version
   - Otherwise, use the current/upcoming version based on the Monday date

### Step 2: Fetch Sprint Data

Run the fetch script located at `scripts/fetch_sprint_data.py` relative to this skill. Execute it directly (not via `python`) to invoke uv via the shebang:

```bash
./scripts/fetch_sprint_data.py --fix-version rhoai-3.5.EA2
```

The script outputs JSON to stdout containing:
- All issues (Features, Initiatives, Epics, Stories) for the fix version
- Issues grouped by squad using team field mapping (customfield_10001)
- Status counts and metrics per squad
- Epic-specific analysis with parent feature tracking

### Step 3: Interpret the JSON into a Sprint Planning Document

Analyze the JSON output and generate a markdown document with the following sections:

#### Executive Summary
- Total epic count for the fix version
- Status breakdown (Closed, In Progress, New, To Do)
- Code freeze date and readiness alerts
- Overall risk assessment

#### Squad-by-Squad Breakdown

For each squad with work assigned, create a section with:
- **Epic count by status**
- **Clickable links** to all epics, grouped by status:
  - Closed epics (nested bullet list with links)
  - In Progress epics (nested bullet list with links)
  - New epics (nested bullet list with links)
- **Parent features** being tracked
- **Contextual questions** based on patterns in the data:
  - Capacity warnings if many new epics near code freeze
  - Questions about old work still open
  - Blocker and dependency questions
  - Specific issues identified (duplicates, unclear ownership, etc.)

#### Cross-Squad Analysis
- Positive indicators (good progress, clear ownership)
- Risk flags (capacity concerns, blocked work, stale items)
- Recommendations for the planning call
- Code freeze readiness assessment

#### Output
Save the markdown to `~/sprint-planning-YYYY-MM-DD.md` where YYYY-MM-DD is the Monday date.

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

## Converting to Google Doc (Optional)

To create a polished Google Doc from the generated markdown, use the included script.

### One-Time Setup

1. **Install Python dependencies:**
   ```bash
   python3 -m venv ~/.google-docs-env
   source ~/.google-docs-env/bin/activate
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. **Set up Google Docs API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Enable Google Docs API and Google Drive API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials JSON to `~/.google-docs-credentials.json`

3. **First run will authenticate:**
   ```bash
   source ~/.google-docs-env/bin/activate
   python3 scripts/create-google-doc.py ~/sprint-planning-YYYY-MM-DD.md
   ```
   Browser opens for authorization (one-time)

### Daily Usage

```bash
source ~/.google-docs-env/bin/activate
python3 scripts/create-google-doc.py ~/sprint-planning-YYYY-MM-DD.md
```

This creates a professionally formatted Google Doc with:
- Proper heading hierarchy
- Nested bullets for epic lists
- Clickable Jira links
- Professional spacing

## Example Workflow

**Sunday evening or Monday morning:**

1. Generate sprint planning analysis:
   ```text
   run aipcc ecosystems sprint planning
   ```

2. (Optional) Convert to Google Doc:
   ```bash
   source ~/.google-docs-env/bin/activate
   python3 scripts/create-google-doc.py ~/sprint-planning-2026-06-08.md
   ```

3. Share markdown or Google Doc link with squad leads 30+ minutes before Monday call

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

The fetch script handles:
- Missing environment variables (JIRA_API_TOKEN, JIRA_EMAIL) with clear error messages
- Missing or invalid configuration file at ~/.claude/sprint-planning-config.json
- Jira API failures (authentication, permissions, network errors)
- Empty results (no issues found for the fix version)

The skill interpretation handles:
- Missing squad assignments (creates "Unassigned" section)
- Empty squad data (only includes squads with work)
- Malformed JSON from the fetch script (reports error to user)

## Related Documentation

- Full README: See `README.md` in this skill directory
- Configuration: `~/.claude/sprint-planning-config.json`
