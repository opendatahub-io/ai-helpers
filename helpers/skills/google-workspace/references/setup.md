# gws CLI Setup

These instructions are for Red Hat employees using Google Workspace via their
corporate accounts.

One-time setup for the [Google Workspace CLI](https://github.com/googleworkspace/cli).

## Before Starting: Gather User Preferences

Before walking through the steps, ask the user for the following:

1. **Install method** -- Homebrew, npm, Cargo, Nix, or pre-built binary?
2. **GCP project name** -- What name for their Google Cloud project? (e.g. `username-gws`)
3. **Google email** -- Their Google account email (used for OAuth consent support email and test user)
4. **App name** -- What to call the OAuth app on the consent screen? (e.g. `gws CLI`)
5. **Which Google services** -- Which APIs do they need? (Drive, Docs, Sheets, Slides, Gmail, Calendar, etc.)

Use these answers throughout the remaining steps. If the user doesn't have a preference for project name or app name, suggest sensible defaults.

## Prerequisites

- A Google account with Workspace access
- One of: Homebrew, Node.js 18+, Rust toolchain, or Nix

## Step 1: Install

Use the install method the user chose:

| Method | Command |
|--------|---------|
| Homebrew (macOS/Linux) | `brew install googleworkspace-cli` |
| npm | `npm install -g @googleworkspace/cli` |
| Cargo (from source) | `cargo install --git https://github.com/googleworkspace/cli --locked` |
| Nix | `nix run github:googleworkspace/cli` |
| Pre-built binary | Download from [GitHub Releases](https://github.com/googleworkspace/cli/releases) |

Verify: `gws --help`

## Step 2: Create a GCP Project

1. Go to https://console.cloud.google.com/projectcreate
2. Name it the project name the user chose
3. Parent resource: **Default Projects**
4. Click Create
5. Note the **Project ID** (the text slug shown under the project name, not the numeric Project Number)

Find your Project ID at https://console.cloud.google.com/home/dashboard or in the project selector dropdown.

**IMPORTANT:** Do NOT use a shared project (e.g. `agentspace-301617`). Create your OWN project -- you need your own for OAuth credentials.

## Step 3: Configure OAuth Consent Screen

URL: `https://console.cloud.google.com/apis/credentials/consent?project=YOUR_PROJECT_ID`

1. User Type: **External** (this is the "Audience" setting, different from the credential type in Step 4)
2. App name: the app name the user chose
3. Support email: the user's Google email
4. Click through and Save all steps
5. Go to **Test users** tab -> Add users -> add the user's Google email

## Step 4: Create OAuth Desktop Credentials

URL: `https://console.cloud.google.com/apis/credentials?project=YOUR_PROJECT_ID`

1. **Create Credentials** -> **OAuth client ID**
2. Application type: **Desktop app** (different from the "External" setting in Step 3)
3. Click Create
4. Download the JSON file (`client_secret_*.json`)
5. Save it:

```bash
mkdir -p ~/.config/gws
mv ~/Downloads/client_secret_*.json ~/.config/gws/client_secret.json
```

## Step 5: Enable APIs

Enable only the APIs the user selected. Replace `YOUR_PROJECT_ID` in the URLs:

| Service | Enable URL |
|---------|-----------|
| Drive | `https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=YOUR_PROJECT_ID` |
| Docs | `https://console.developers.google.com/apis/api/docs.googleapis.com/overview?project=YOUR_PROJECT_ID` |
| Sheets | `https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=YOUR_PROJECT_ID` |
| Gmail | `https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=YOUR_PROJECT_ID` |
| Calendar | `https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview?project=YOUR_PROJECT_ID` |
| Slides | `https://console.developers.google.com/apis/api/slides.googleapis.com/overview?project=YOUR_PROJECT_ID` |

Only show the rows matching the services the user chose. Click **Enable** on each. If one is skipped, gws returns a `403 accessNotConfigured` error with a direct link to enable the missing API.

## Step 6: Authenticate

Do NOT run `gws auth setup` -- it automates via gcloud and tends to fail.

**IMPORTANT: Do NOT run this command for the user.** The `gws auth login` command opens an OAuth flow where the user must interactively select scopes. Tell the user to run this command themselves in their terminal:

```bash
gws auth login -s <comma-separated services they chose>
```

Example: if they chose Drive, Docs, and Sheets -> `gws auth login -s drive,docs,sheets`

Keep it under ~25 scopes -- Google rejects consent for unverified apps with too many.

Tell the user what to expect when the browser opens:
1. "Google hasn't verified this app" -> click **Advanced** -> **Go to \<app name\> (unsafe)**. Expected for testing-mode apps.
2. Approve the requested scopes
3. They should see a success message

Wait for the user to confirm they completed the login before proceeding.

## Step 7: Verify

```bash
gws drive files list --params '{"pageSize": 5}'
```

You should see your recent Drive files.

## Adding Scopes Later

```bash
gws auth logout
gws auth login -s drive,docs,sheets,gmail,calendar
```

Goes through the consent flow again with the expanded scope set.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Failed to set project` validationError | Used `gws auth setup` | Skip it. Use `gws auth login -s drive` |
| Too many scopes / consent rejected | Too many scopes selected | Use `-s` to limit: `gws auth login -s drive,docs` |
| Access blocked / 403 on login | Not added as test user | Add your email under OAuth consent -> Test users |
| "User type: External" not visible | Using a shared org project | Create your OWN project at console.cloud.google.com/projectcreate |
| 403 accessNotConfigured | API not enabled | Click the `enable_url` from the error -> Enable -> wait 30s |
| Confusing "External" vs "Desktop app" | Two different screens | External = OAuth consent audience. Desktop app = credential type |
| `redirect_uri_mismatch` | OAuth client not created as Desktop app | Delete the client, recreate as **Desktop app**, download new JSON |
