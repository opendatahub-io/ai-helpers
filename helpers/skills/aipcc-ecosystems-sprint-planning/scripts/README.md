# Sprint Planning Scripts

This directory contains scripts for the AIPCC Ecosystems sprint planning workflow.

## fetch_sprint_data.py

Fetches sprint planning data from AIPCC Jira project and outputs structured JSON.

### Prerequisites

- Python 3.7+ with `uv` package manager
- Jira API access to redhat.atlassian.net
- Configuration file at `~/.claude/sprint-planning-config.json`

### Environment Variables

```bash
export JIRA_API_TOKEN='your-token-here'
export JIRA_EMAIL='your-email@redhat.com'
```

**How to get a Jira API token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "Sprint Planning Script")
4. Copy the token and set it in your environment

### Usage

```bash
./scripts/fetch_sprint_data.py --fix-version rhoai-3.5.EA2
```

With custom config file:
```bash
./scripts/fetch_sprint_data.py --fix-version rhoai-3.5.EA3 --config ~/custom-config.json
```

### Output

Outputs JSON to stdout with:
```json
{
  "fix_version": "rhoai-3.5.EA2",
  "project": "AIPCC",
  "squads": {
    "CUDA": {
      "total_issues": 15,
      "total_epics": 8,
      "epic_statuses": {
        "Closed": 2,
        "In Progress": 3,
        "New": 3
      },
      "epics": [...]
    }
  },
  "metadata": {
    "fetched_at": "2026-06-05T...",
    "total_issues": 120,
    "total_epics": 38
  }
}
```

### Error Handling

The script exits with status 1 on errors:
- Missing environment variables (JIRA_API_TOKEN, JIRA_EMAIL)
- Missing or invalid config file
- Jira authentication failures
- Network or API errors

Errors are printed to stderr with clear instructions.

---

## create-google-doc.py

Converts the sprint planning markdown document to a professionally formatted Google Doc.

### Prerequisites

- Python 3.7+
- Google Cloud project with Docs API and Drive API enabled
- OAuth credentials downloaded

### Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv ~/.google-docs-env
   source ~/.google-docs-env/bin/activate
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. **Get Google API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing
   - Enable "Google Docs API" and "Google Drive API"
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Select "Desktop app" as application type
   - Download credentials JSON
   - Save as `~/.google-docs-credentials.json`

3. **First run (authentication):**
   ```bash
   source ~/.google-docs-env/bin/activate
   python3 create-google-doc.py ~/sprint-planning-2026-06-08.md
   ```
   - Browser opens for Google authorization
   - Sign in and grant permissions
   - Token saved to `~/.google-docs-token.pickle` for future use

### Usage

```bash
source ~/.google-docs-env/bin/activate
python3 create-google-doc.py <path-to-markdown-file>
```

Example:
```bash
python3 create-google-doc.py ~/sprint-planning-2026-06-08.md
```

### Output

Creates a Google Doc with:
- ✅ Proper heading hierarchy (H1, H2, H3)
- ✅ Nested bullet points (properly indented sub-bullets)
- ✅ Clickable Jira links
- ✅ Professional spacing (reduced gaps between sections)
- ✅ Bold text formatting preserved

Returns the Google Doc URL for sharing.

### Troubleshooting

**"Credentials file not found"**
- Ensure `~/.google-docs-credentials.json` exists
- Re-download from Google Cloud Console if needed

**"Authorization expired"**
- Delete `~/.google-docs-token.pickle`
- Re-run script to re-authorize

**"Permission denied"**
- Ensure APIs are enabled in Google Cloud Console
- Wait a few minutes for API enablement to propagate

---

## Workflow Integration

**Typical sprint planning prep workflow:**

1. **Fetch data:**
   ```bash
   ./scripts/fetch_sprint_data.py --fix-version rhoai-3.5.EA2 > sprint-data.json
   ```

2. **Let Claude interpret:**
   Skill uses the JSON to generate `~/sprint-planning-2026-06-08.md`

3. **(Optional) Create Google Doc:**
   ```bash
   source ~/.google-docs-env/bin/activate
   python3 scripts/create-google-doc.py ~/sprint-planning-2026-06-08.md
   ```

4. **Share with squad leads** 30+ minutes before Monday planning call
