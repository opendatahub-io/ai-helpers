# Google Docs Conversion Script

Converts the sprint planning markdown document to a professionally formatted Google Doc.

## Prerequisites

- Python 3.7+
- Google Cloud project with Docs API and Drive API enabled
- OAuth credentials downloaded

## Setup

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

## Usage

```bash
source ~/.google-docs-env/bin/activate
python3 create-google-doc.py <path-to-markdown-file>
```

Example:
```bash
python3 create-google-doc.py ~/sprint-planning-2026-06-08.md
```

## Output

Creates a Google Doc with:
- ✅ Proper heading hierarchy (H1, H2, H3)
- ✅ Nested bullet points (properly indented sub-bullets)
- ✅ Clickable Jira links
- ✅ Professional spacing (reduced gaps between sections)
- ✅ Bold text formatting preserved

Returns the Google Doc URL for sharing.

## Troubleshooting

**"Credentials file not found"**
- Ensure `~/.google-docs-credentials.json` exists
- Re-download from Google Cloud Console if needed

**"Authorization expired"**
- Delete `~/.google-docs-token.pickle`
- Re-run script to re-authorize

**"Permission denied"**
- Ensure APIs are enabled in Google Cloud Console
- Wait a few minutes for API enablement to propagate
