# Sprint Planning Prep Skill

Automates Monday sprint planning preparation for the Ecosystems team (8 squads across AIPCC project).

**Time saved:** 30-45 minutes of manual Jira review and document creation

---

## What It Does

1. **Pulls Jira data** - Queries AIPCC project for Features, Initiatives, Epics, Stories
2. **Analyzes by squad** - Groups work by 8 accelerator squads (CUDA, ROCm, Gaudi, etc.)
3. **Generates questions** - Creates contextual questions based on patterns (old work, capacity, blockers)
4. **Creates planning doc** - Outputs formatted markdown with squad-by-squad breakdowns
5. **Converts to Google Doc** - Professional formatted document ready to share with squad leads

---

## How to Use

### Quick Usage (2 steps)

**Step 1: Generate sprint planning analysis**

Just say to Claude:
```
run sprint planning prep
```

This will:
- Calculate next Monday's date and sprint week
- Pull all rhoai-3.5.EA2 (or current fix version) work from Jira
- Analyze by squad with epic/story counts
- Generate markdown file: `~/sprint-planning-YYYY-MM-DD.md`

**Step 2: Create Google Doc**

In your terminal:
```bash
cd ~
source google-docs-env/bin/activate
python3 create-google-doc-final.py sprint-planning-YYYY-MM-DD.md
```

This creates a polished Google Doc with:
- ✅ Proper heading hierarchy
- ✅ Nested bullets for epic lists
- ✅ Clickable Jira links
- ✅ Professional spacing and layout
- ✅ Ready to share with squad leads

---

## Output Format

The generated document includes:

### Executive Summary
- Total epic count for current fix version
- Status breakdown (Closed/In Progress/New/To Do)
- Code freeze alerts
- Risk assessment

### Squad-by-Squad Breakdown

For each of 8 squads:
- **Epic count by status**
- **Clickable links** to all epics (grouped by Closed/In Progress/New)
- **Parent features** tracked
- **Contextual questions** based on data patterns:
  - Capacity warnings (too many new epics near code freeze)
  - Old work still open (from previous fix versions)
  - Blockers and dependencies
  - Specific issues identified (duplicate work, unclear ownership)

### Cross-Squad Analysis
- Positive indicators
- Risk flags
- Recommendations
- Code freeze readiness assessment

---

## Configuration

**Config file:** `~/.claude/sprint-planning-config.json`

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

**To modify:** Edit the config file directly. Changes take effect immediately.

---

## First-Time Setup

### Prerequisites
✅ Atlassian MCP configured (already done)
✅ Access to AIPCC Jira project (already have)
✅ Python 3.14+ (already installed)

### Google Docs Setup (One-Time, 15-20 minutes)

**If you haven't set up Google Docs API yet, follow:** `/Users/belwell/GOOGLE-DOCS-SETUP.md`

Quick summary:
1. Enable Google Docs API and Google Drive API in Google Cloud Console
2. Create OAuth credentials and download to `~/.google-docs-credentials.json`
3. Install Python packages in virtual environment
4. Run script once to authorize

**Detailed instructions:** See "Google Docs Setup Guide" section below.

---

## Example Workflow

**Sunday evening or Monday morning:**

```bash
# In Claude Code, say:
run sprint planning prep

# You'll get:
# ✅ Sprint planning doc ready!
# 📄 /Users/belwell/sprint-planning-2026-06-08.md

# Then in terminal:
cd ~
source google-docs-env/bin/activate
python3 create-google-doc-final.py sprint-planning-2026-06-08.md

# You'll get:
# ✅ Success!
# 📄 Google Doc created: https://docs.google.com/document/d/ABC123.../edit
```

**Before Monday call:**
1. Review the Google Doc
2. Share link with squad leads (30+ min before call)
3. Use doc during call to walk through each squad's priorities

**During Monday call:**
- 6-8 minutes per squad
- Walk through priorities using the doc
- Squad leads ask clarifying questions
- Assign unassigned work

**After Monday call:**
- Squad leads meet with their teams
- Break down epics into stories
- Assign work to team members

---

## Troubleshooting

### "run sprint planning prep" doesn't work
- Make sure you're in Claude Code, not a regular terminal
- The skill is invoked by asking Claude, not running a command

### Google Doc creation fails
- Check that virtual environment is activated: `source ~/google-docs-env/bin/activate`
- Verify credentials exist: `ls -la ~/.google-docs-credentials.json`
- Re-authorize if needed (delete `~/.google-docs-token.pickle` and run again)

### Wrong fix version analyzed
- The skill auto-detects the next upcoming fix version
- If incorrect, the analysis logic may need adjustment
- Currently targets: rhoai-3.5.EA2

### Squad mapping incorrect
- Edit `~/.claude/sprint-planning-config.json`
- Update the `team_mapping` section with correct team IDs
- Changes take effect on next run

### Missing squads in output
- Check if squad has work in current fix version
- Verify team field is set in Jira for those epics
- Unassigned epics appear in "Unassigned Work" section

---

## Files Created

**Config:**
- `~/.claude/sprint-planning-config.json` - Squad mappings and settings
- `~/.google-docs-credentials.json` - Google API credentials (one-time setup)
- `~/.google-docs-token.pickle` - OAuth token (auto-refreshed)

**Scripts:**
- `~/create-google-doc-final.py` - Markdown to Google Doc converter
- `~/google-docs-env/` - Python virtual environment

**Output:**
- `~/sprint-planning-YYYY-MM-DD.md` - Markdown planning document
- Google Doc (in your Google Drive)

---

## Advanced Usage

### Manual markdown editing
If you need to edit the markdown before creating the Google Doc:

```bash
# Generate markdown
# (In Claude Code) run sprint planning prep

# Edit the markdown
code ~/sprint-planning-2026-06-08.md

# Create Google Doc from edited version
source ~/google-docs-env/bin/activate
python3 create-google-doc-final.py sprint-planning-2026-06-08.md
```

### Archive old planning docs
```bash
mkdir -p ~/sprint-planning-archive
mv ~/sprint-planning-*.md ~/sprint-planning-archive/
```

### Use different fix version
Currently auto-detects. To analyze a different version, ask Claude:
```
run sprint planning prep for rhoai-3.5.EA3
```

---

## Design Specs

Full design documentation:
- Process design: `/Users/belwell/docs/superpowers/specs/2026-05-29-ecosystems-sprint-planning-design.md`
- Skill design: `/Users/belwell/docs/superpowers/specs/2026-06-05-sprint-planning-skill-design.md`

---

## Future Enhancements

**Planned improvements:**
- Automatic Jira status updates (move issues from New → To Do)
- Slack integration (auto-post doc link to channel)
- Historical tracking (velocity metrics, completion rates)
- Story-level breakdown in the doc
- Capacity modeling per squad

**Already completed:**
- ✅ Automated Jira data pulling
- ✅ Squad-by-squad analysis
- ✅ Contextual question generation
- ✅ Google Docs integration
- ✅ Professional formatting

---

---

## See Also

- **Google Docs Setup Guide:** `/Users/belwell/GOOGLE-DOCS-SETUP.md` - Full setup instructions for first-time users
- **Process Design Spec:** `/Users/belwell/docs/superpowers/specs/2026-05-29-ecosystems-sprint-planning-design.md`
- **Skill Design Spec:** `/Users/belwell/docs/superpowers/specs/2026-06-05-sprint-planning-skill-design.md`

---

**Maintained by:** Beth White, Manager - Ecosystems Team  
**Last updated:** June 5, 2026  
**Version:** 1.0
